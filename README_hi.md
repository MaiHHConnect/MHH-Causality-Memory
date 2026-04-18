# CausaMem - कारण स्मृति प्रणाली

> अपने AI एजेंट को आजीवन स्मृति दें | AI एजेंटों के लिए कारण स्मृति प्रणाली

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [हिन्दी](README_hi.md)

---

## पृष्ठभूमि

CausaMem AI एजेंटों के लिए एक स्वतंत्र स्मृति प्रणाली है। विकास पूर्ण होने के बाद, हमने [Claude-Mem](https://github.com/thedotmack/claude-mem) का संदर्भ लिया और इसकी मुख्य **AI-संरचित संपीड़न** क्षमता को लागू किया, जिसे **कारण-तर्क** के साथ विस्तारित किया।

## मुख्य विशेषताएं

| विशेषता | विवरण |
|---------|--------|
| 4-परत स्मृति | घटनाएं → समयरेखा → संबंध → सारांश |
| AI-संरचित संपीड़न | decided/learned/completed/next_steps स्वतः निष्कर्ष |
| कारण-तर्क | cause (कारण) / effect (प्रभाव) का अनुमान |
| 3-इंजन खोज | वेक्टर + FTS5 + कारण श्रृंखला |
| पठनीय Wiki | Obsidian Wiki प्रारूप |
| प्रकार टैग | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## त्वरित प्रारंभ

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "हमने स्मृति प्रणाली पर चर्चा की, 4-परत संरचना का निर्णय लिया"
python gbrain.py causal "smriti"
```

## श्रेय

[Claude-Mem](https://github.com/thedotmack/claude-mem) से प्रेरित।

## लाइसेंस

MIT License
