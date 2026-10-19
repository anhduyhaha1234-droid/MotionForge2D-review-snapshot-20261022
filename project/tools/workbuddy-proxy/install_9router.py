import datetime
import json
import pathlib
import sqlite3
import uuid


DB = pathlib.Path.home() / "AppData" / "Roaming" / "9router" / "db" / "data.sqlite"
PREFIX = "wb"
MODEL_ID = "hy4-preview"
NODE_NAME = "WorkBuddy HY4"
BASE_URL = "http://127.0.0.1:8787/v1"


def main() -> None:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    existing = conn.execute(
        "SELECT id FROM providerNodes WHERE json_extract(data, '$.prefix') = ?",
        (PREFIX,),
    ).fetchone()
    if existing:
        node_id = existing["id"]
    else:
        node_id = f"openai-compatible-chat-{uuid.uuid4()}"
        node_data = json.dumps(
            {"prefix": PREFIX, "apiType": "chat", "baseUrl": BASE_URL},
            separators=(",", ":"),
        )
        conn.execute(
            "INSERT INTO providerNodes(id,type,name,data,createdAt,updatedAt) VALUES(?,?,?,?,?,?)",
            (node_id, "openai-compatible", NODE_NAME, node_data, now, now),
        )

    connection = conn.execute(
        "SELECT id FROM providerConnections WHERE provider = ? LIMIT 1",
        (node_id,),
    ).fetchone()
    if not connection:
        connection_data = json.dumps(
            {
                "defaultModel": MODEL_ID,
                "apiKey": "sk-workbuddy-local",
                "testStatus": "unavailable",
                "providerSpecificData": {
                    "prefix": PREFIX,
                    "apiType": "chat",
                    "baseUrl": BASE_URL,
                    "nodeName": NODE_NAME,
                    "connectionProxyEnabled": False,
                    "connectionProxyUrl": "",
                    "connectionNoProxy": "",
                },
            },
            separators=(",", ":"),
        )
        conn.execute(
            "INSERT INTO providerConnections(id,provider,authType,name,email,priority,isActive,data,createdAt,updatedAt) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()), node_id, "apikey", NODE_NAME, None, 1, 1,
                connection_data, now, now,
            ),
        )

    model_key = f"{PREFIX}|{MODEL_ID}|llm"
    model_value = json.dumps(
        {"providerAlias": PREFIX, "id": MODEL_ID, "type": "llm", "name": MODEL_ID},
        separators=(",", ":"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO kv(scope,key,value) VALUES('customModels',?,?)",
        (model_key, model_value),
    )
    conn.commit()

    print(f"node_id={node_id}")
    print(f"model={PREFIX}/{MODEL_ID}")
    print("existing providers and models were not updated or deleted")


if __name__ == "__main__":
    main()
