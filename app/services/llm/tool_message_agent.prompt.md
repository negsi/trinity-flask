`message_agent`: Delegiert Aufgaben an einen Sub-Agenten (`target_agent_id`, `message`).
   - Nur Ziel-IDs aus "Verfügbare Agenten" nutzen. Kein Selbstaufruf.
   - **Keine Re-Executions / Fallbacks:** Die Rückgabe von `message_agent` ist final. Bei eigener Werkzeugausstattung Aufgaben direkt selbst ausführen statt weiterzuverteilen.
   - **Ergebnisübernahme:** Die Antwort des Sub-Agenten zwingend in die finale Nutzerantwort übernehmen (keine bloße Floskel "Erledigt"). Kein nachfolgendes `message_llm` zur reinen "Zusammenfassung", es sei denn, mehrere Quellen werden synthetisiert.