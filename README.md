# RAG Data Generator

Un'applicazione completa per la generazione automatica di dati RAG (Retrieval-Augmented Generation) attraverso l'integrazione di due modelli LLM. Il sistema crea record strutturati contenenti requisiti di codifica, soluzioni e metadati per training e fine-tuning di modelli di intelligenza artificiale.

## Panoramica del Progetto

Questo progetto implementa un generatore di dati RAG che utilizza una pipeline a due stadi:

1. **Stage 1 (Model X)**: Genera requisiti di codifica specifici con vincoli di sicurezza
2. **Stage 2 (Model Y)**: Produce soluzioni di codifica PHP/HTML complete con commenti

Il sistema è progettato per creare dataset di alta qualità per addestramento di modelli LLM in **qualsiasi dominio** (programmazione, cucina, scienza, etc.), con particolare attenzione all'auto-training: i modelli LLM utilizzano quanto appreso per generare nuovi problemi e nuove soluzioni, creando un ciclo virtuoso di apprendimento continuo.

## Caratteristiche Principali

### 🤖 Doppio Modello LLM
- **Model X**: Specializzato in architettura PHP e sicurezza, genera intenti di codifica
- **Model Y**: Sviluppatore esperto PHP/HTML, produce codice pulito e commentato
- Supporto per endpoint HTTP personalizzabili

### 🌐 Formati di Output Multipli
- **JSON**: Formato strutturato per training e analisi dati
- **HTML Web Format**: Pagine web complete, moderne e SEO-friendly pronte per pubblicazione
- Generazione automatica di titoli e contenuti formattati
- Template responsive con design professionale

### 🎨 Configurazione RAG Generica
- **Dominio Personalizzabile**: Supporta qualsiasi argomento (programmazione, cucina, scienza, etc.)
- **Prompt Dinamici**: Adattamento automatico dei prompt in base al dominio
- **Preset Predefiniti**: 7 preset pronti all'uso per diversi domini tecnologici
- **Constraint Editabile**: Campo completamente personalizzabile per vincoli specifici

## Installazione

```bash
# Python 3.8+
python3 --version

# Installazione dipendenze
pip install requests tkinter
```

## Utilizzo

### Modalità GUI (Default)

```bash
python3 rag_generator.py
```

### Modalità CLI

```bash
python3 rag_generator.py --cli
```

## Link Utili

- [USAGE_GUIDE.md](./USAGE_GUIDE.md) - Guida dettagliata all'uso
- [project_showcase.html](./project_showcase.html) - Articolo completo sul progetto

## Licenza

Questo progetto è rilasciato con licenza MIT.

---

**Versione:** 2.0.0  
**Data Ultima Modifica:** 2025-12-29  
**Stato:** Production Ready 🚀