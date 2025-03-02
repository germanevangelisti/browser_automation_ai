# Browser Automation Agent

This project is a browser automation agent that uses OpenAI's language model to translate natural language commands into structured JSON actions for browser automation. The agent is capable of interacting with web pages using Playwright, executing actions such as opening URLs, inputting text, clicking elements, and taking screenshots.

## Features

- **Natural Language Processing**: Utilizes OpenAI's language model to convert user commands into JSON actions.
- **Browser Automation**: Executes actions in a browser using Playwright, including opening URLs, filling forms, clicking elements, and more.
- **WebSocket Live View**: Provides a live view of the browser session via WebSocket.
- **Command History**: Maintains a history of executed commands with links to screenshots.
- **Fallback Selectors**: Uses alternative selectors if the primary selector fails to find an element.

## Components

### `agent.py`

- **BrowserAgent Class**: The core class responsible for managing browser sessions and executing actions.
  - `translate_to_json(command: str)`: Translates a natural language command into JSON actions.
  - `execute_from_text(command: str)`: Translates and executes a command.
  - `execute_actions(actions)`: Executes a list of actions in the browser.
  - `try_alternative_selectors_for_click(action)`: Attempts to use alternative selectors if a click action fails.
  - `move_mouse_humanlike(x, y, radius=20, loops=1)`: Simulates human-like mouse movements.
  - `delay_action(milliseconds=500)`: Introduces a delay between actions to simulate human behavior.
  - `screenshot()`: Takes a screenshot of the current browser view.

### `browser-agent-ui/src/App.js`

- **React Application**: Provides a user interface for interacting with the BrowserAgent.
  - **Command Input**: Allows users to input natural language commands.
  - **Command History**: Displays a history of executed commands with links to screenshots.
  - **Live View**: Shows a live view of the browser session.
  - **WebSocket Connection**: Manages a WebSocket connection to receive live updates from the browser.

## Setup and Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies**:
   - For the backend (Python):
     ```bash
     pip install -r requirements.txt
     ```
   - For the frontend (React):
     ```bash
     cd browser-agent-ui
     npm install
     ```

3. **Environment Variables**:
   - Set the `OPENAI_API_KEY` environment variable with your OpenAI API key.

4. **Run the Backend**:
   ```bash
   python web_server.py
   ```

5. **Run the Frontend**:
   ```bash
   cd browser-agent-ui
   npm start
   ```

## Usage

- **Enter Commands**: Use the input field in the UI to enter natural language commands.
- **View Command History**: Check the command history for past commands and view associated screenshots.
- **Live View**: Switch to the live view tab to see real-time updates from the browser.

## Future Enhancements

- **Improved Selector Identification**: Enhance the AI's ability to identify and use the most reliable selectors.
- **Error Handling**: Improve error handling and recovery for failed actions.
- **Additional Actions**: Support more complex actions and interactions with web pages.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 