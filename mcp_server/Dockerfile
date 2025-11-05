FROM python:3.11-slim

WORKDIR /app

COPY mcp_server/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server/server.py /app/

EXPOSE 8080

CMD ["python", "server.py"]
