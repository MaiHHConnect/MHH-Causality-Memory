# CausaMem - Αιτιώδες Σύστημα Μνήμης

> Δώστε στον AI Agent σας μνήμη δια βίου | Αιτιώδες Σύστημα Μνήμης για AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Ελληνικά](README_el.md)

---

## Πλαίσιο

CausaMem είναι ένα ανεξάρτητο σύστημα μνήμης για AI Agents. Μετά την ανάπτυξη, αναφερθήκαμε στο [Claude-Mem](https://github.com/thedotmack/claude-mem) και υλοποιήσαμε την κεντρική του λειτουργία **AI-δομημένης συμπίεσης**, επεκταμένη με **αιτιώδη συλλογιστική**.

## Κύριες Λειτουργίες

| Λειτουργία | Περιγραφή |
|-----------|-----------|
| Μνήμη 4 επιπέδων | Γεγονότα → Χρονοδιάγραμμα → Σχέσεις → Περιλήψεις |
| AI-δομημένη συμπίεση | Αυτόματη εξαγωγή decided/learned/completed/next_steps |
| Αιτιώδης συλλογιστική | Συνάγει cause (αιτία) / effect (αποτέλεσμα) |
| Αναζήτηση 3 κινητήρων | Διάνυσμα + FTS5 + Αιτιώδης αλυσίδα |
| Ευανάγνωστο Wiki | Μορφή Obsidian Wiki |
| Ετικέτες τύπου | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Γρήγορη Εκκίνηση

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Συζητήσαμε το σύστημα μνήμης, αποφασίσαμε να χρησιμοποιήσουμε δομή 4 επιπέδων"
python gbrain.py causal "mnhmh"
```

## Ευχαριστίες

Εμπνευσμένο από το [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Άδεια

MIT License
