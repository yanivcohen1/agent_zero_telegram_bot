import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

# Import the handlers from the bot script
import agent_zero_telegram_bot as bot

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.from_user = MagicMock(spec=User)
    update.message.from_user.id = bot.MY_ID
    update.message.from_user.first_name = "TestUser"
    update.message.chat_id = 12345
    update.message.reply_text = AsyncMock()
    return update

@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    context.bot.send_document = AsyncMock()
    context.job_queue = MagicMock()
    context.job_queue.run_repeating = MagicMock()
    context.job_queue.get_jobs_by_name = MagicMock()
    context.job_queue.jobs = MagicMock()
    return context

async def run_and_await_tasks(coro):
    """Helper to run a coroutine and await any asyncio tasks it creates."""
    original_create_task = asyncio.create_task
    created_tasks = []
    
    def mock_create_task(c):
        task = original_create_task(c)
        created_tasks.append(task)
        return task
        
    with patch('asyncio.create_task', side_effect=mock_create_task):
        await coro
        
    if created_tasks:
        await asyncio.gather(*created_tasks)
    return created_tasks

@pytest.mark.asyncio
async def test_unauthorized_user(mock_update, mock_context):
    # Set a different user ID
    unauthorized_id = 999999
    test_message = "Hello"
    print(f"\n[TEST] Sending message from unauthorized user ({unauthorized_id}): '{test_message}'")
    mock_update.message.from_user.id = unauthorized_id
    mock_update.message.text = test_message
    
    created_tasks = await run_and_await_tasks(bot.handle_request(mock_update, mock_context))
    
    # Should not process the request
    assert len(created_tasks) == 0
    mock_context.bot.send_message.assert_not_called()
    print("[TEST] Request was correctly ignored for unauthorized user.")

@pytest.mark.asyncio
@patch('agent_zero_telegram_bot.requests.post')
async def test_handle_request_text(mock_post, mock_update, mock_context):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Mocked Agent Zero response"}
    mock_post.return_value = mock_response

    test_message = "Hello Agent Zero"
    print(f"\n[TEST] Sending message: '{test_message}'")
    mock_update.message.text = test_message
    
    await run_and_await_tasks(bot.handle_request(mock_update, mock_context))
        
    # Check if the bot sent a message
    assert mock_context.bot.send_message.call_count >= 2
    
    # Print all messages sent by the bot during this test
    print("\n[TEST] Received messages from bot:")
    for call in mock_context.bot.send_message.call_args_list:
        args, kwargs = call
        text = kwargs.get('text', args[0] if args else '')
        print(f"  -> {text}")
    
    # Check the content of the last message sent
    args, kwargs = mock_context.bot.send_message.call_args
    assert "Completed!" in kwargs.get('text', '') or "Completed!" in args[0] if args else True

@pytest.mark.asyncio
async def test_schedule_command(mock_update, mock_context):
    test_message = "/schedule test 60 do something"
    print(f"\n[TEST] Sending command: '{test_message}'")
    mock_update.message.text = test_message
    mock_context.args = ["test", "60", "do", "something"]
    mock_context.job_queue.get_jobs_by_name.return_value = []
    
    await run_and_await_tasks(bot.schedule_command(mock_update, mock_context))
    
    mock_context.job_queue.run_repeating.assert_called_once()
    mock_update.message.reply_text.assert_awaited_once()
    args, kwargs = mock_update.message.reply_text.call_args
    response_text = kwargs.get('text', args[0] if args else '')
    print(f"\n[TEST] Received response: '{response_text}'")
    assert "added" in response_text

@pytest.mark.asyncio
async def test_schedule_command_missing_args(mock_update, mock_context):
    test_message = "/schedule test"
    print(f"\n[TEST] Sending command: '{test_message}'")
    mock_update.message.text = test_message
    mock_context.args = ["test"]
    
    await run_and_await_tasks(bot.schedule_command(mock_update, mock_context))
    
    mock_update.message.reply_text.assert_awaited_once()
    args, kwargs = mock_update.message.reply_text.call_args
    response_text = kwargs.get('text', args[0] if args else '')
    print(f"\n[TEST] Received response: '{response_text}'")
    assert "Usage" in response_text

@pytest.mark.asyncio
async def test_stop_schedule_command(mock_update, mock_context):
    test_message = "/stopschedule test"
    print(f"\n[TEST] Sending command: '{test_message}'")
    mock_update.message.text = test_message
    mock_context.args = ["test"]
    
    mock_job = MagicMock()
    mock_context.job_queue.get_jobs_by_name.return_value = [mock_job]
    
    await run_and_await_tasks(bot.stop_schedule_command(mock_update, mock_context))
    
    mock_job.schedule_removal.assert_called_once()
    mock_update.message.reply_text.assert_awaited_once()
    args, kwargs = mock_update.message.reply_text.call_args
    response_text = kwargs.get('text', args[0] if args else '')
    print(f"\n[TEST] Received response: '{response_text}'")
    assert "stopped" in response_text

@pytest.mark.asyncio
async def test_help_command(mock_update, mock_context):
    test_message = "/help"
    print(f"\n[TEST] Sending command: '{test_message}'")
    await run_and_await_tasks(bot.help_command(mock_update, mock_context))
    
    mock_update.message.reply_text.assert_awaited_once()
    args, kwargs = mock_update.message.reply_text.call_args
    response_text = kwargs.get('text', args[0] if args else '')
    print(f"\n[TEST] Received response:\n{response_text}")
    assert "OpenClaw/Agent Zero Bot Help" in response_text

@pytest.mark.asyncio
async def test_new_command(mock_update, mock_context):
    test_message = "/new"
    print(f"\n[TEST] Sending command: '{test_message}'")
    await run_and_await_tasks(bot.new_command(mock_update, mock_context))
    
    mock_update.message.reply_text.assert_awaited_once_with(
        "✨ New session started. Conversation history cleared."
    )
    args, kwargs = mock_update.message.reply_text.call_args
    response_text = kwargs.get('text', args[0] if args else '')
    print(f"\n[TEST] Received response: '{response_text}'")
    assert bot.context_id is None

@pytest.mark.asyncio
async def test_stop_command(mock_update, mock_context):
    test_message = "/stop"
    print(f"\n[TEST] Sending command: '{test_message}'")
    await run_and_await_tasks(bot.stop_command(mock_update, mock_context))
    
    mock_update.message.reply_text.assert_awaited_once_with(
        "🛑 Conversation stopped and session cleared."
    )
    args, kwargs = mock_update.message.reply_text.call_args
    response_text = kwargs.get('text', args[0] if args else '')
    print(f"\n[TEST] Received response: '{response_text}'")
    assert bot.context_id is None

@pytest.mark.asyncio
async def test_restart_command(mock_update, mock_context):
    test_message = "/restart"
    print(f"\n[TEST] Sending command: '{test_message}'")
    await run_and_await_tasks(bot.restart_command(mock_update, mock_context))
    
    mock_update.message.reply_text.assert_awaited_once_with(
        "🔄 Session restarted. Ready for a new conversation."
    )
    args, kwargs = mock_update.message.reply_text.call_args
    response_text = kwargs.get('text', args[0] if args else '')
    print(f"\n[TEST] Received response: '{response_text}'")
    assert bot.context_id is None

@pytest.mark.asyncio
@patch('agent_zero_telegram_bot.requests.post')
async def test_handle_photo(mock_post, mock_update, mock_context, tmp_path):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Mocked Agent Zero photo response"}
    mock_post.return_value = mock_response

    # Create a dummy image file
    import os
    test_image_path = tmp_path / "test_image.jpg"
    test_image_path.write_bytes(b"dummy image data")
    
    # Mock the photo file
    mock_photo_file = AsyncMock()
    mock_photo_file.download_to_drive = AsyncMock()
    
    # Mock the photo array in the message
    mock_photo = MagicMock()
    mock_photo.get_file = AsyncMock(return_value=mock_photo_file)
    mock_update.message.photo = [mock_photo]
    mock_update.message.caption = "Test caption"
    mock_update.message.message_id = 123
    
    print(f"\n[TEST] Sending photo with caption: '{mock_update.message.caption}'")
    
    # Patch PIC_DIR to use our temporary directory
    with patch('agent_zero_telegram_bot.PIC_DIR', str(tmp_path)):
        # We need to mock open to return our dummy file data when it tries to read the downloaded file
        # because download_to_drive is mocked and won't actually create the file
        import builtins
        original_open = builtins.open
        
        def mock_open(file, mode='r', *args, **kwargs):
            # The bot uses the caption as filename (spaces are kept, only special chars are replaced)
            if str(file).endswith("Test caption.jpg") and 'r' in mode:
                return original_open(test_image_path, mode, *args, **kwargs)
            return original_open(file, mode, *args, **kwargs)
            
        with patch('builtins.open', mock_open):
            await run_and_await_tasks(bot.handle_photo(mock_update, mock_context))
        
    # Check if the bot sent a confirmation message
    assert mock_update.message.reply_text.call_count >= 1
    
    print("\n[TEST] Received responses:")
    for call in mock_update.message.reply_text.call_args_list:
        args, kwargs = call
        text = kwargs.get('text', args[0] if args else '')
        print(f"  -> {text}")
        
    # Check if the bot sent a message about the task
    assert mock_context.bot.send_message.call_count >= 2
    
    print("\n[TEST] Received messages from bot:")
    for call in mock_context.bot.send_message.call_args_list:
        args, kwargs = call
        text = kwargs.get('text', args[0] if args else '')
        print(f"  -> {text}")

@pytest.mark.asyncio
async def test_get_pic_command(mock_update, mock_context, tmp_path):
    # Create a dummy image file in the temp directory
    import os
    test_image_name = "test_image.jpg"
    test_image_path = tmp_path / test_image_name
    test_image_path.write_bytes(b"dummy image data")
    
    test_message = f"get pic {test_image_name}"
    print(f"\n[TEST] Sending message: '{test_message}'")
    mock_update.message.text = test_message
    
    # Patch PIC_DIR to use our temporary directory
    with patch('agent_zero_telegram_bot.PIC_DIR', str(tmp_path)):
        await run_and_await_tasks(bot.handle_request(mock_update, mock_context))
        
    # Check if the bot sent the photo
    mock_context.bot.send_photo.assert_awaited_once()
    args, kwargs = mock_context.bot.send_photo.call_args
    caption = kwargs.get('caption', '')
    print(f"\n[TEST] Received photo with caption: '{caption}'")
    assert f"Here is {test_image_name}" in caption
