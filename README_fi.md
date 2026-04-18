# CausaMem - Kausaalinen Muistijärjestelmä

> Anna AI-agentillesi elinikäinen muisti | Kausaalinen muistijärjestelmä AI-agenteille

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Suomi](README_fi.md)

---

## Tausta

CausaMem on itsenäinen muistijärjestelmä AI-agenteille. Kehityksen jälkeen viittasimme [Claude-Memiin](https://github.com/thedotmack/claude-mem) ja toteutimme sen ydinominaisuuden **AI-rakenteisen pakkauksen**, laajennettuna **kausaalisella päättelyllä**.

## Pääominaisuudet

| Ominaisuus | Kuvaus |
|-----------|--------|
| 4-kerroksinen muisti | Tapahtumat → Aikajana → Suhteet → Yhteenvedot |
| AI-rakenteinen pakkaus | Poimii automaattisesti decided/learned/completed/next_steps |
| Kausaalinen päättely | Johtaa cause (syy) / effect (seuraus) |
| 3-moottorinen haku | Vektori + FTS5 + Kausaalinen ketju |
| Luettava Wiki | Obsidian Wiki -muoto |
| Tyyppi-tagit | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Pika-aloitus

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Keskitimme muistijärjestelmästä, päätimme käyttää 4-kerroksista rakennetta"
python gbrain.py causal "muisti"
```

## Kiitokset

Inspiroitunut [Claude-Mem](https://github.com/thedotmack/claude-mem):stä.

## Lisenssi

MIT License
