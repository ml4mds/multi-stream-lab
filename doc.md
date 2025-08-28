# Transfer Images between the Client and the Server

After starting the server,
the client and the server communicate with each other through a WebSocket connection.
Here is a detailed overview of the WebSocket API.

## Connection Lifecycle

- **Initiation**: The client will attempt to connect to `ws://{host}/ws` only if the user clicks the "Run" button.
- **Termination**: The connection is terminated under several conditions:
  - The user clicks the "Stop" button.
  - The server sends a "completion" message.
  - The server sends any message the frontend cannot parse or doesn't understand.
  - A network error occurs.

## Communication Protocol Overview

The communication is message-based.
Every message, in both directions, is expected to be a **JSON string**,
which is defined as follows:

```json
{
  "type": "data" | "action",
  "data": { ... } | "string"
}
```

### Message 1: Initial Configuration

This message is sent from the client to the server once the connection is established.
It is to inform the server which dataset and algorithm the user has selected.
The definition is as follows:
```json
{
  "type": "data",
  "data": {
    "dataset": "string",
    "algorithm": "string"
  }
}
```

### Message 2: Labels

This message is sent from the server to the client to confirm the server receives correct dataset and algorithm,
and then return a list of labels.
The definition is as follows:
```json
{
  "type": "data",
  "data": {
    "labels": "string",
    "algorithm": "string"
  }
}
```

### Message 2: Start Signal

The frontend sends this message *after* it has successfully received the list of `labels` from your server.

*   **Purpose:** To confirm that the UI is ready and to signal the backend to start sending the actual image data. This creates a simple handshake, preventing the backend from sending images before the UI is prepared to display them.
*   **Structure:**
    ```json
    {
      "type": "action",
      "data": "start"
    }
    ```

---

### 4. Server-to-Client Messages (What Your API Must Send)

Your API is expected to send three types of messages to the frontend in a specific order.

#### Message 1: Labels for UI Setup

This **must be the first message** you send to the client after receiving its initial configuration. The frontend's logic is critically dependent on receiving labels before any images.

*   **Purpose:** To provide the frontend with the "categories" or "tabs" it needs to render.
*   **Structure:**
    ```json
    {
      "type": "data",
      "data": {
        "labels": ["CPU Usage", "Memory", "Network I/O", "Disk Activity"]
      }
    }
    ```
    *   `labels`: An array of strings. The order of strings in this array will determine the order of the tabs in the UI.

#### Message 2: Image Data Stream

These messages should only be sent *after* the client has sent the `"action": "start"` message back to you. You can send these as a stream of updates, one for each label.

*   **Purpose:** To provide the visual data for each tab.
*   **Structure:**
    ```json
    {
      "type": "data",
      "data": {
        "image": {
          "label": "CPU Usage",
          "content": "iVBORw0KGgoAAAANSUhEUgAAB... (the base64 string)"
        }
      }
    }
    ```
    *   `image.label`: A string that **must exactly match** one of the labels sent in the initial `labels` message. This is used by the frontend to place the image in the correct tab.
    *   `image.content`: A **Base64-encoded string** of a JPEG image. The frontend will prepend this with `data:image/jpeg;base64,` to render it.

#### Message 3: Completion Signal

This should be the final message you send when the process is successfully finished.

*   **Purpose:** To inform the frontend that the task is complete.
*   **Structure:**
    ```json
    {
      "type": "action",
      "data": "completion"
    }
    ```
*   **Frontend's Reaction:** Upon receiving this, the frontend will display a success message and close the WebSocket connection from its end.

### Summary of the Expected Message Flow

Here is the play-by-play interaction:

1.  **Client:** Connects to `ws://localhost:8889/ws`.
2.  **Client:** Sends `{ "type": "data", "data": { "dataset": "...", "algorithm": "..." } }`.
3.  **Server:** Receives config, prepares the job.
4.  **Server:** Sends `{ "type": "data", "data": { "labels": ["label1", "label2"] } }`.
5.  **Client:** Receives labels, builds UI tabs.
6.  **Client:** Sends `{ "type": "action", "data": "start" }`.
7.  **Server:** Receives start signal.
8.  **Server:** Starts streaming image data, sending one message at a time:
    *   `{ "type": "data", "data": { "image": { "label": "label1", "content": "..." } } }`
    *   `{ "type": "data", "data": { "image": { "label": "label2", "content": "..." } } }`
    *   ...(can be repeated for updates)
9.  **Server:** Finishes the process.
10. **Server:** Sends `{ "type": "action", "data": "completion" }`.
11. **Client:** Receives completion, shows a success modal, and closes the connection.

If your backend follows this contract, the frontend should work as intended.
