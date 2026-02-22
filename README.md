🔐 Secure Chat Application (RSA + AES Hybrid Encryption)
========================================================

A production-style **End-to-End Encrypted Chat Application** built using **Hybrid Cryptography (RSA + AES-GCM)** with a modern client-server architecture.

This project demonstrates practical implementation of cryptographic principles including secure key exchange, authenticated encryption, and zero-knowledge server design.

🚀 Features
-----------

*   2048-bit RSA keypair generation (client-side)
    
*   AES-256-GCM authenticated message encryption
    
*   Hybrid cryptography (RSA for key exchange + AES for data)
    
*   Zero-knowledge server (cannot decrypt messages)
    
*   Modern GUI built with PyQt5
    
*   FastAPI backend with RESTful APIs
    
*   SQLite database (server + local history)
    
*   Integrity protection using AES-GCM authentication tag
    
*   Encrypted traffic validation (Wireshark tested)
    

🏗 Architecture
---------------

### Client (PyQt5)

*   RSA Key Manager
    
*   AES-GCM Encryptor/Decryptor
    
*   GUI Chat Interface
    
*   Local SQLite history database
    
*   Private key stored locally (never transmitted)
    

### Server (FastAPI)

*   User Registration API
    
*   Public Key Directory
    
*   Encrypted Message Storage
    
*   SQLite database (users + messages)
    
*   Zero access to plaintext messages
    

🔄 Cryptographic Workflow
-------------------------

### 🔐 Sending a Message

1.  Fetch recipient's RSA public key
    
2.  Generate random 256-bit AES session key
    
3.  Encrypt message using AES-GCM
    
4.  Wrap AES key using recipient's RSA public key (OAEP)
    
5.  Send:
    
    *   Ciphertext
        
    *   Wrapped AES key
        
    *   Nonce
        
    *   Authentication tag
        
6.  Server stores encrypted data only
    

### 🔓 Receiving a Message

1.  Retrieve encrypted message from server
    
2.  Unwrap AES key using private RSA key
    
3.  Decrypt ciphertext using AES-GCM
    
4.  Verify authentication tag
    
5.  Display plaintext in GUI
    

🛡 Security Model
-----------------

### Protected Against:

*   Network eavesdropping
    
*   Message tampering
    
*   Server compromise (zero-knowledge design)
    
*   Man-in-the-middle attacks on message content
    

### Not Protected Against:

*   Compromised client device
    
*   Private key theft
    
*   Endpoint attacks (keyloggers, malware)
    

🧰 Tech Stack
-------------

ComponentTechnologyBackendFastAPIFrontendPyQt5EncryptionRSA (2048-bit), AES-256-GCMDatabaseSQLiteLanguagePython 3

📂 Project Structure
--------------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   secure-chat/  │  ├── client/  │   ├── gui.py  │   ├── rsa_manager.py  │   ├── aes_engine.py  │   ├── local_db.py  │  ├── server/  │   ├── main.py  │   ├── models.py  │   ├── database.py  │  ├── data.sqlite  ├── requirements.txt  └── README.md   `

⚙️ Installation & Setup
-----------------------

### 1️⃣ Clone Repository

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   git clone https://github.com/yourusername/secure-chat.git  cd secure-chat   `

### 2️⃣ Install Dependencies

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   pip install -r requirements.txt   `

### 3️⃣ Start Backend Server

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   cd backend  uvicorn server:app --reload --host 0.0.0.0 --port 8000   `

Server runs at:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   http://127.0.0.1:8000   `

### 4️⃣ Run Client Application

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   cd client  python3 client_pyqt.py   `

🔍 API Documentation
--------------------

FastAPI automatically generates API docs at:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   http://127.0.0.1:8000/docs   `

📈 Future Improvements
----------------------

*   HTTPS/TLS support
    
*   Encrypted file sharing
    
*   Group chat with secure group keys
    
*   Multi-device synchronization
    
*   PostgreSQL migration
    
*   Mobile application version
    

🎓 Learning Outcomes
--------------------

This project demonstrates:

*   Practical hybrid cryptography implementation
    
*   Secure key management
    
*   Zero-knowledge architecture design
    
*   Authenticated encryption (AES-GCM)
    
*   RESTful API development
    
*   Secure client-server communication design
    

📜 References
-------------

*   RSA (Rivest, Shamir, Adleman – 1978)
    
*   NIST AES Standard (FIPS-197)
    
*   RSA-OAEP
    
*   AES-GCM
    
*   TLS 1.3 Specification
    

👨‍💻 Authors
-------------

*   Aditya Rana
    
*   Daksh Sharma
    
*   Prateek
    

Information Security LabB.Tech CSE – Jaypee Institute of Information Technology
