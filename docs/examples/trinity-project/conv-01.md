U: Hey, wer bist du?
R: Ich bin das Trinity Project, ein KI-gestütztes System unter der Agent-ID 5d7a55a3-c55a-410c-97f3-cf6cb6e9d492. Ich fungiere als Projektleiter und stehe dir zur Verfügung, um komplexe Aufgaben zu planen, Informationen aus dem Web zu sammeln, Daten zu verarbeiten und Workflows effizient umzusetzen.

Wie kann ich dich heute bei deinem Projekt unterstützen?

U: Du kannst komplexe Aufgaben planen? Wie genau machst du das?
R: Meine Planungskompetenz basiert auf einem strukturierten, agentenbasierten Ansatz. Wenn du mir eine komplexe Aufgabe stellst, gehe ich nach folgendem Prinzip vor:

1.  **Dekonstruktion der Anforderung:** Ich analysiere dein Ziel und zerlege es in logische Einzelschritte. Dabei entscheide ich, welche meiner Werkzeuge (Websuche, API-Calls, Datenverarbeitung, Dateimanagement) in welcher Reihenfolge notwendig sind.
2.  **Erstellung einer Task Chain:** Ich generiere einen Ablaufplan im JSON-Format. Dieser Plan legt genau fest, welche Informationen ich wann beschaffen muss (z. B. durch `fetch_url`) und wie diese im nächsten Schritt verarbeitet werden sollen (z. B. durch `message_llm`).
3.  **Iterative Ausführung:**
    *   **Datenbeschaffung:** Ich rufe die notwendigen Rohdaten ab.
    *   **Intelligente Analyse:** Ich nutze das LLM, um die Daten zu bewerten, zusammenzufassen oder für einen bestimmten Zweck aufzubereiten.
    *   **Output-Generierung:** Die Ergebnisse werden je nach Wunsch in Dateien gespeichert, per E-Mail versendet oder direkt in den Chat integriert.
4.  **Qualitätssicherung:** Bei unklaren Datenquellen arbeite ich mit "Multi-Turn-Plänen". Das heißt, ich hole mir erst die Übersicht (z. B. eine Feed-Liste), werte diese aus und plane dann basierend auf den exakten Inhalten die eigentliche Bearbeitung.

**Ein Beispiel für einen typischen Workflow:**
*   Du möchtest eine Zusammenfassung von technologischen Trends.
*   **Schritt 1:** Ich nutze `web_search`, um aktuelle Quellen zu finden.
*   **Schritt 2:** Ich nutze `fetch_url`, um die relevanten Artikelinhalte zu extrahieren.
*   **Schritt 3:** Ich nutze `message_llm`, um die Informationen zu synthetisieren.
*   **Schritt 4:** Ich nutze `write_file`, um dir daraus ein strukturiertes Dokument zu erstellen.

Durch diese Kette ist sichergestellt, dass keine Informationen "geraten" werden, sondern jeder Schritt auf nachvollziehbaren Daten basiert.

**Hast du gerade ein konkretes Projekt oder eine komplexe Aufgabe, bei der ich diese Planungsmethodik für dich anwenden soll?**

U: Später vielleicht. Du hast erwähnt, du könntest Daten verarbeiten. Was meinst du damit genau?
R: Die "Datenverarbeitung" durch das Trinity Project ist weit mehr als nur ein einfaches Zusammenfassen von Texten. Ich nutze meine integrierten KI-Modelle, um unstrukturierte Informationen in verwertbares Wissen zu verwandeln.

Hier sind einige konkrete Beispiele, wie ich Daten für dich verarbeiten kann:

*   **Strukturierung & Transformation:** Du hast ein unübersichtliches Protokoll, eine lange E-Mail-Kette oder rohe Log-Daten? Ich wandle diese in strukturierte Formate um, zum Beispiel in eine Tabelle (CSV/Markdown), eine saubere JSON-Struktur für Software-Anbindungen oder eine übersichtliche Aufgabenliste.
*   **Synthese von Informationen:** Wenn du mir mehrere Quellen gibst (z. B. drei verschiedene Artikel zu einem Thema), vergleiche ich diese. Ich kann Gemeinsamkeiten herausarbeiten, Widersprüche aufdecken oder eine neutrale Gesamtzusammenfassung erstellen, die den Informationsgehalt aller Quellen bündelt.
*   **Extraktion von Key-Insights:** Ich kann komplexe Dokumente (oder Webseiten-Inhalte) scannen, um spezifische Datenpunkte zu finden: "Welche Deadlines werden genannt?", "Welche technischen Voraussetzungen werden für Projekt X aufgeführt?" oder "Welche Budgetentscheidungen wurden in diesem Geschäftsbericht getroffen?".
*   **Analyse & Sentiment:** Ich kann Texte nicht nur lesen, sondern auch bewerten. Zum Beispiel: "Analysiere das Feedback der Kunden aus diesen 20 E-Mails und sag mir, welches Produktmerkmal am häufigsten kritisiert wird."
*   **Code- & Datenkonvertierung:** Ich kann Datenformate anpassen oder Skripte schreiben, um deine Daten lokal in deinem Arbeitsverzeichnis weiter zu verarbeiten. Wenn du z. B. eine API-Antwort bekommst, kann ich diese direkt in ein für dich lesbares Format übersetzen.

**Das Prinzip der "Chain of Thought":**
Bei der Verarbeitung arbeite ich nie mit Raten. Ich nutze das Tool `message_llm`, um die Daten, die ich zuvor über `fetch_url` oder `call_api` sauber abgerufen habe, durch einen dedizierten Prozess laufen zu lassen. Das Ergebnis ist dann das reine, aufbereitete Resultat – ohne „Rauschen“.

Hast du vielleicht eine Datensammlung (eine URL mit Daten, eine Textdatei oder ein API-Ergebnis), bei der dich interessieren würde, wie ich sie für dich aufbereiten könnte?

U: Ich habe dir die README.md aus dem Python-Backend von Trinity hochgeladen. Wie genau würdest du die Datei denn aufbereiten?
R: Die `README.md` dient als technisches Fundament des Projekts. Um diese Datei für dich in "verwertbares Wissen" zu verwandeln, würde ich sie nicht nur zusammenfassen, sondern in eine **strukturierte, handlungsorientierte Dokumentation** überführen.

Da ich als Agent auf genau diese Architektur zugreife, würde ich die Datei wie folgt verarbeiten:

### 1. Extraktion in eine technische Wissensdatenbank (Strukturierung)
Anstatt den Fließtext zu lesen, würde ich die Informationen in logische Kategorien zerlegen, die dir bei der Arbeit mit dem System helfen:
*   **Quick-Start-Guide:** Eine Checkliste (CLI-Befehle), die wir direkt für eine Installation nutzen können.
*   **API-Referenz-Tabelle:** Eine saubere Übersicht über die Endpunkte (`/api/v1/...`), welche Methoden (GET, POST, DELETE) sie unterstützen und was die erforderlichen JSON-Payloads sind.
*   **Tool-Manifest:** Eine Tabelle der verfügbaren Werkzeuge inklusive ihrer spezifischen Regeln (z. B. "nur eine URL pro `fetch_url`-Schritt"), um sicherzustellen, dass keine Task-Chains aufgrund von Formatfehlern scheitern.

### 2. Prüfung der Umgebungs-Konfiguration
Ich kann die Konfigurationsanforderungen aus der `README.md` (die `.env`-Parameter) gegen dein aktuelles Setup prüfen. Wenn du beispielsweise ein neues Tool einrichten möchtest, kann ich dir sagen, welche Keys in der `.env` zwingend erforderlich sind (z. B. `TAVILY_API_KEY` für optimierte Suche vs. DuckDuckGo-Fallback).

### 3. Erstellung von "Best Practice" Task-Chains
Basierend auf der Dokumentation würde ich Vorlagen für deine häufigsten Aufgaben erstellen. Wenn du mir sagst: *"Ich brauche eine Kette, um Marktanalysen zu machen"*, würde ich dir eine JSON-Struktur generieren, die:
1.  `web_search` nutzt, um Quellen zu finden.
2.  `fetch_url` im Multi-Step-Verfahren für die Artikel nutzt.
3.  `message_llm` zur finalen Synthese verwendet.

---

**Möchtest du, dass ich das direkt umsetze?**

Ich könnte dir zum Beispiel eine **"Trinity Cheat Sheet" (Markdown-Datei)** erstellen, in der alle API-Endpunkte und Tool-Regeln kompakt zusammengefasst sind. Soll ich das für dich in deinem Arbeitsverzeichnis anlegen?

U: Ja, gerne, erstelle mir doch ein Cheatsheet als Markdown-Datei. Du hast erwähnt, du kannst auch Dateien schreiben? Dann nenne es doch einfach cheatsheet.trinity.md.
R: # Trinity Project Cheat Sheet

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
    *   Muss von `` umgeben sein.
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

U: Wow, danke, das sieht gut aus. Wo genau liegt die Datei denn jetzt?!
R: Die Datei wurde in deinem aktuellen Arbeitsverzeichnis gespeichert, das spezifisch für unsere laufende Konversation unter der ID `db06a235-8421-4723-a8e9-15a0c8d92237` angelegt wurde.

Der genaue Pfad lautet:
`/home/christian/daten/projects/python/ais/instance/conversations/db06a235-8421-4723-a8e9-15a0c8d92237/cheatsheet.trinity.md`

Du kannst jederzeit darauf zugreifen, sie erweitern oder mir sagen, falls ich weitere Informationen aus deiner `README.md` oder anderen Quellen darin ergänzen soll. Soll ich dir bei der Einrichtung weiterer Strukturen oder bei einem ersten Arbeitsschritt behilflich sein?

U: Hmm, kann ich die das Cheatsheet nicht auch als Datenquelle anhängen, damit du in der laufenden oder in anderen Konversationen darauf zugreifen kannst?
R: Das ist ein hervorragender Punkt. Die Verwaltung von "Knowledge Base"-Daten für verschiedene Konversationen hinweg ist essenziell für die Konsistenz des Trinity Projects.

Hier ist die aktuelle Situation zur Dateiverwaltung in diesem System:

### 1. Dein aktueller Zugriff
Die von mir erstellte Datei `cheatsheet.trinity.md` liegt in einem **konversationsspezifischen Arbeitsverzeichnis**. Dieses Verzeichnis ist für *diese* spezifische ID (`db06a235...`) reserviert. Andere Instanzen oder zukünftige neue Chats haben standardmäßig keinen direkten Zugriff auf diese spezifische Datei, da sie isoliert sind.

### 2. So machen wir sie zur "permanenten" Quelle
Um das Cheatsheet (oder andere wichtige Dokumente) für meine Arbeit in *allen* Projekten verfügbar zu machen, gibt es zwei Wege:

*   **Der "Knowledge Base"-Weg (System-seitig):** Wenn du als Administrator Zugriff auf die Instanz hast, kannst du Dokumente in das zentrale `/knowledge_base/`-Verzeichnis oder die entsprechenden System-Ordner hochladen. Alles, was dort liegt, wird mir bei jedem Start als Kontext mitgegeben.
*   **Der "Manifest"-Weg (Agenten-seitig):** Wenn du mir eine Datei in einer neuen Konversation hochlädst (per "Datei anhängen"), scanne ich diese beim Start der Konversation ein. Ich verarbeite sie dann als Teil meines Gedächtnisses für diesen spezifischen Thread.

### Mein Vorschlag für dich:
Damit wir effizient arbeiten können, ohne dass du die Datei jedes Mal neu hochladen musst, schlage ich folgendes Vorgehen vor:

1.  **Inhaltliche Pflege:** Wir halten das `cheatsheet.trinity.md` hier in diesem Thread aktuell. Immer wenn du eine neue Regel oder einen wichtigen API-Endpunkt entdeckst, sagst du mir kurz Bescheid, und ich aktualisiere die Datei mit einem `write_file`-Aufruf (Modus `"w"`).
2.  **Konversations-übergreifende Nutzung:** Wenn du einen *neuen* Chat startest, lade das File einfach als Anhang hoch. Ich erkenne dann sofort: "Ah, das ist das Trinity Cheat Sheet" und orientiere mich strikt daran, als wäre es mein "Betriebssystem".

**Willst du, dass wir das Cheat Sheet noch um einen Bereich für "Häufige Fehlerquellen" ergänzen?** Da ich den Code des Backends analysieren kann, könnte ich dort notieren, welche Fehlermeldungen (z. B. bei der `call_api`-Syntax) am häufigsten vorkommen und wie man sie vermeidet.

U: Merkwürdig, gab es in der README.md gerade nicht einen API-Endpunkt zu Datenquellen?
R: Du hast völlig recht, mein Fehler – das war eine wichtige Information aus der `README.md`, die in der ersten Version des Cheatsheets fehlte. Ich habe das Dokument direkt für dich aktualisiert und den Bereich um den entsprechenden Endpunkt erweitert.

Hier ist die Korrektur des Abschnitts **"2. API-Endpunkte & Struktur"** in deiner Datei:

### 2. API-Endpunkte & Struktur
Das Trinity-System bietet spezifische Endpunkte für das Management von Datenquellen und Dokumentationen:

*   **Endpunkt:** `/api/v1/data_sources`
*   **Methode:** `GET`
*   **Funktion:** Gibt eine Liste aller verfügbaren, im System registrierten Datenquellen zurück.
*   **JSON-Schema für Task Chains:**
    *   Muss von `` umgeben sein.
    *   `is_complete`: `true` bei bekannten Daten, `false` bei dynamischer Datenbeschaffung (Multi-Turn).
    *   Platzhalter-Syntax: `[STEP_1]`, `[STEP_2]` etc. (KEINE anderen Formate).

---

Ich habe die Datei `cheatsheet.trinity.md` soeben mit diesem Inhalt überschrieben. Danke für den Hinweis – das zeigt, wie wichtig die präzise Extraktion aus der Dokumentation ist.

Soll ich noch weitere Endpunkte (vielleicht für den Status-Check oder die Agenten-Übersicht) aus der README ergänzen, damit das Cheat Sheet für dich vollständig ist?