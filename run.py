import os
import sys
import json
from dotenv import load_dotenv
from run_workflow import run_workflow

# 1️⃣ Load environment variables
load_dotenv()


def main():
    """
    Runs the AI workflow using JSON input (from n8n or CLI).
    All parameters must be provided via JSON input - no defaults.
    """

    try:
        # 2️⃣ Read JSON input (from n8n or CLI)
        if not sys.stdin.isatty():
            raw_input = sys.stdin.read().strip()
            if not raw_input:
                raise ValueError("No input provided. JSON input is required.")
            data = json.loads(raw_input)
        else:
            raise ValueError("No input provided. JSON input is required via stdin.")

        # 3️⃣ Validate and extract required inputs
        if "topic" not in data:
            raise ValueError("Required field 'topic' missing from input")

        topic = data["topic"]
        mode = data.get("mode", "lead")  # Only mode has a sensible default
        recipient_name = data.get("recipient_name", "")
        sender_company_summary = data.get("sender_company_summary", "")
        max_results = int(data.get("max_results", 5))
        html = data.get("html", False)

        # Sender info - must be provided or will use empty values
        sender_info = data.get("sender_info", {})

        # 4️⃣ Run the workflow
        result = run_workflow(
            topic=topic,
            mode=mode,
            recipient_name=recipient_name,
            sender_company_summary=sender_company_summary,
            sender_info=sender_info,
            max_results=max_results,
            html=html
        )

        # prepare payload
        # Check if workflow succeeded
        if not result.get("success", True):
            # Workflow returned error
            print(json.dumps(result, indent=2))
            return

        if mode == "lead":
            payload = {
                "success": True,
                "mode": mode,
                "summary": result.get("summary", ""),
                "email": result.get("email", {}),
            }
        else:
            payload = {
                "success": True,
                "mode": mode,
                "summary": result.get("summary", ""),
                "content": result.get("content", ""),
            }

        # 5️⃣ Return JSON output (stdout)
        print(json.dumps(payload, indent=2))

    except ValueError as e:
        # 6️⃣ Input validation error
        print(
            json.dumps(
                {"success": False, "error_type": "InputError", "message": str(e)},
                indent=2,
            )
        )

    except json.JSONDecodeError as e:
        # 7️⃣ JSON parsing error
        print(
            json.dumps(
                {
                    "success": False,
                    "error_type": "JSONError",
                    "message": f"Invalid JSON: {str(e)}",
                },
                indent=2,
            )
        )

    except Exception as e:
        # 8️⃣ Catch-all error handler (to prevent n8n from breaking)
        print(
            json.dumps(
                {"success": False, "error_type": "RunnerError", "message": str(e)},
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
