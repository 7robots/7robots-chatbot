# 7robots-chatbot
 
 ## Overview

 This software can be used to serve an AI Chatbot interface to provide answers about your documents. It leverages OpenAI's new Agents framework to provide the GAI back-end. Similarly, it also leverages vector storage provided by the OpenAI to store your documents.

 ## Prerequisites

 - an OpenAI API key and credits on the OpenAI platform for both API usage and storage.
 - Python 3.11 or higher
 - Pip (to install software dependencies)

## OpenAI considerations

- this project only works with OpenAI directly. A future release may add the ability to use custom endpoints (like Azure).
- This project's admin interface will be able to add/modify/delete all vector stores accessible by your API key
- As such, you should consider creating a new project in the OpenAI platform, creating a project API key within that project, and only leverage vector stores inside that project.
- You should be able to create and manage your vector store in either the OpenAI platform or via this chatbot's admin interface.

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
cp config.yaml.example config.yaml
```

## Initial Configuration

Edit config.yaml to:

- add your OpenAI key
- add your vector storage ID if you already know it (if not, you'll be able to discover it or create a new one via the admin interface)
- name your chatbot

(note: all three of these functions can also be done via the admin web interface, but it's probably easier to do them in the config.yaml file before you start the service. Should you need to change any of these three settings, the chatbot application will automatically load the settings without the need to stop/start again)

```
assistant:
  name: My Assistant
openai:
  api_key: your_openai_api_key_here
  vector_store_id: your_vector_store_id_here
```

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
