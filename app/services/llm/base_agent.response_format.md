Schema zur Planung von Aufgaben:
###START_JSON_RESPONSE###
{
  "response": {
    "type": "task_chain",
    "summary": "Gesamtziel des Plans",
    "is_complete": true,
    "steps": [
      {
        "step": 1,
        "description": "Was genau getan werden muss",
        "tool": "system_name_des_skills",
        "parameters": {
          "key": "value"
        }
      }
    ]
  }
}
###END_JSON_RESPONSE###

Steuerung von "is_complete":
- Setze "is_complete": true, wenn dieser Plan die ursprüngliche Anforderung des Benutzers volständig beantwortet.
- Setze "is_complete": false, wenn du erst Daten beschaffen oder extrahieren musst (z. B. URLs aus einem RSS-Feed/einer HTML-Seite lesen), um im nächsten Durchlauf die eigentlichen Ziel-Schritte mit den echten Daten zu planen.
