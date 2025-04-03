# 7robots-chatbot
 
## Software Installation




1. Clone the repository:

```bash
git clone https://github.com/7robots/7robots-chatbot.git
cd 7robots-chatbot
```

2. Setup virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```


3. Install required packages and stage configuration file
```bash
pip install -r requirements.txt
mv config.yaml.example config.yaml
```

## Initial Configuration

## Optional: if you have already know your OpenAI API key and your Vector Store ID, you can add them here. Otherwise, you can do it later via the admin web page. Edit config.yaml and add your keys.
openai:
  api_key: your_openai_api_key_here
  vector_store_id: your_vector_store_id_here


## Start the FastAPI server with uvicorn
fastapi run agent.py

## Admin Page
Admin Panel: http://localhost:8000/admin


## Accessing the Chat application: 

Main Chat Interface: http://localhost:8000/webchat


## Troubleshooting
Missing Dependencies: If you encounter errors about missing packages, install them individually with pip install package_name

API Key Issues: Ensure your OpenAI API key is valid and has the necessary permissions for vector storage operations

Vector Store ID Issues: Make sure the vector store ID exists in your OpenAI account

File Upload Problems: Check that your OpenAI account has sufficient credits and permissions for file operations

## Next Steps
Upload your knowledge base files via the File Management page
Configure your agent's behavior through the Admin Panel
Customize the chat interface by modifying the index.html file

## Shutting Down
To stop the application, press Ctrl+C in the terminal where it's running.

To deactivate the virtual environment when you're done working:
deactivate

For further assistance or to report issues, please open an issue on the GitHub repository.