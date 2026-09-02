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
          "file_path": "beispiel.py",
          "content": "REF:PAYLOAD_STEP_1"
        }
      }
    ]
  }
}
###END_JSON_RESPONSE###
###START_CONTENT_PAYLOADS###
<<<PAYLOAD_STEP_1>>>
Unmaskierter Quellcode, Templates oder Fließtext hier einfügen...
<<<END_PAYLOAD_STEP_1>>>
###END_CONTENT_PAYLOADS###

Steuerung von "is_complete":
- Setze "is_complete": false, wenn du erst Daten beschaffen oder extrahieren musst (z. B. URLs aus einem RSS-Feed/einer HTML-Seite lesen), um im nächsten Durchlauf die eigentlichen Ziel-Schritte mit den echten Daten zu planen. Plane in diesem Fall AUSSCHLIESSLICH den einen Abruf-Schritt (Step 1). Erstelle KEINE spekulativen Folgeschritte im selben Plan!
- Setze "is_complete": true, wenn dieser Plan die ursprüngliche Anforderung des Benutzers vollständig beantwortet oder dir bereits alle konkreten Ziel-URLs vorliegen, um den Plan inklusive finaler Auswertung komplett durchzuplanen.

Regeln für Schritte & Payloads:
- Die Schritt-Nummerierung ("step") innerhalb eines JSON-Plans MUSS zwingend fortlaufend bei 1 beginnen (1, 2, 3, 4...).
- **Entkopplung von Code & langen Texten:** Bettet NIEMALS mehrzeiligen Quellcode, komplexe Strings mit Anführungszeichen oder Dateiinhalte direkt als JSON-String in die Parameter ein.
- Nutze stattdessen als Parameterwert eine Referenz nach dem Schema `"REF:PAYLOAD_STEP_N"` (z. B. `"content": "REF:PAYLOAD_STEP_1"`).
- **Zwingende Payload-Generierung:** Wenn mindestens eine Parameter-Referenz `"REF:PAYLOAD_STEP_N"` verwendet wird, MUSS unmittelbar nach `###END_JSON_RESPONSE###` der `###START_CONTENT_PAYLOADS###`-Block folgen.
- Jeder referenzierte Payload wird darin exakt mit `<<<PAYLOAD_STEP_N>>>` begonnen und mit `<<<END_PAYLOAD_STEP_N>>>` abgeschlossen. Es darf KEIN verwendeter `REF:PAYLOAD_STEP_N`-Schlüssel fehlen.
- Falls der Plan keine `REF:`-Referenzen enthält, entfällt der `###START_CONTENT_PAYLOADS###`-Block vollständig.