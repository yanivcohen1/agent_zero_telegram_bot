FROM mcr.microsoft.com/playwright:v1.41.0-jammy
RUN apt-get update && apt-get install -y python3 python3-pip
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN npm install -g openclaw@latest
COPY . .
CMD ["python3", "bot.py"]
