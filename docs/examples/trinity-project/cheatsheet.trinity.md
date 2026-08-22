# Trinity Project Cheat Sheet

Dieses Dokument dient als zentrale Referenz für die Arbeit mit dem Trinity Project (Agent-ID: 5d7a55a3-c55a-410c-97f3-cf6cb6e9d492).

## 1. Werkzeuge & Nutzungsregeln

| Werkzeug | Funktion | Strikte Regeln |
| :--- | :--- | :--- |
| **fetch_url** | Dokumentinhalt aus dem Web abrufen. | NUR für konkrete URLs verwenden. RSS/Übersichtsseiten MÜSSEN im nächsten Step für JEDEN Artikel einzeln aufgerufen werden. |
| **message_llm** | Auswertung, Zusammenfassung, Transformation. | MUSS bei Datenbeschaffung zwingend als letzter Schritt zur Verarbeitung genutzt werden. KEIN JSON-Output in Unteraufrufen. |
| **write_file** | Erstellen/Ändern von Dateien. | Parameter: `file_path`, `content`, `mode` ("w" oder "a"). |
| **send_email** | Versand von E-Mails. | Unterstützt Platzhalter für Step-Ergebnisse. Bild-Anhänge per Dateinamen explizit angeben. |
| **generate_image** | Bildgenerierung. | Resultierendes Markdown-Bild-Snippet MUSS unverändert in die finale Antwort übernommen werden. |
| **web_search** | Live-Websuche. | Nur bei Fehlen von URLs verwenden. Relevante Links für Folge-Schritte merken. |
| **call_api** | Strukturierte HTTP-Requests. | Speziell für REST-APIs. Bei Auswertung/Zusammenfassung `message_llm` nachschalten. |

## 2. API-Endpunkte & Struktur
Das Trinity-System ist auf eine strukturierte Kommunikation über Task Chains im JSON-Format angewiesen.

*   **JSON-Schema für Task Chains:**
    *   Muss von `###START_JSON_RESPONSE###` und `###END_JSON_RESPONSE###` umgeben sein.
    *   `is_complete`: `true` bei bekannten Daten, `false` bei dynamischer Datenbeschaffung (Multi-Turn).
    *   Platzhalter-Syntax: `[STEP_1]`, `[STEP_2]` etc. (KEINE anderen Formate).

## 3. Konfigurationsvorgaben
*   **Agent-ID:** 5d7a55a3-c55a-410c-97f3-cf6cb6e9d492
*   **Datumsformat:** 2026-08-22 14:30:27 UTC
*   **Dateizugriff:** Alle generierten Dateien werden isoliert im Arbeitsverzeichnis der aktuellen Konversation gespeichert.
*   **Keine Meta-Floskeln:** Bei der Generierung von Code oder Dokumenten (z.B. durch `message_llm`) darf kein einleitender Text (wie "Hier ist dein Code:") oder Abschluss-Text ausgegeben werden.

## 4. Best Practices für komplexe Aufgaben
1.  **Dekonstruktion:** Zerlege Aufgaben in logische Schritte.
2.  **Transparenz:** Nutze `message_llm` immer als Instanz, die Rohdaten (aus `fetch_url` oder `call_api`) in das Zielformat transformiert.
3.  **Vollständigkeit:** Ein Plan darf NIEMALS nur aus Datenbeschaffung bestehen, wenn ein inhaltliches Ergebnis gefordert ist.
4.  **Format-Treue:** Bei der Generierung von Inhalten für Dateien ist strikt auf das angeforderte Format (Markdown, JSON, HTML) zu achten – ohne Markdown-Wrapper bei Code-Generierung, falls das Tool dies vorgibt.