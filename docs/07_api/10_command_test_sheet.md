# 10-Command Test Sheet

Use these commands one-by-one against `POST /unity/voice-command` with payload:

```json
{
	"command": "<one command>",
	"mode": "quick"
}
```

## Commands And Expected Results

1. `what day is it`

- expected: `action=speak`, `intent=time_date`

2. `what time is it now`

- expected: `action=speak`, `intent=time_date`

3. `take me to cs department ta office`

- expected: `action=navigate`, `intent=navigation_start`, destination should map to `ta_office_1`

4. `go to math ta office`

- expected: `action=navigate`, `intent=navigation_start`

5. `navigate to lecture hall a`

- expected: `action=navigate`, `intent=navigation_start`

6. `where is ta office 1`

- expected: `action=navigate`, `intent=navigation_start`

7. `stop navigation`

- expected: `action=cancel_navigation`, `intent=navigation_cancel`

8. `cancel navigation`

- expected: `action=cancel_navigation`, `intent=navigation_cancel`

9. `tell me a joke`

- expected: `action=speak`, `intent=general_query`

10. `take me to mars office`

- expected: `action=speak`, `intent=navigation_unknown_destination`

## Quick Curl Example

```powershell
curl -X POST http://localhost:8000/unity/voice-command \
  -H "Content-Type: application/json" \
  -d '{"command":"what day is it","mode":"quick"}'
```
