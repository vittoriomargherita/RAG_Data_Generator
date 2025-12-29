# RAG Data Generator - Guida all'Uso

## Novità 🎉

L'applicazione ora supporta la **configurazione completa del tipo di dati RAG** generati! Puoi personalizzare completamente i prompt per creare dataset specializzati in diversi domini tecnologici.

## Funzionalità di Configurazione RAG

### 🎯 Perché questa funzione è importante?

Prima l'applicazione era limitata a PHP/HTML con focus su sicurezza. Ora puoi generare dati RAG per:

- **Python Machine Learning** - Integrazione AI/ML, deployment modelli
- **JavaScript Modern Stack** - React, Vue, TypeScript, performance
- **Java Enterprise** - Microservizi, Spring Boot, scalabilità
- **Mobile Development** - React Native, iOS/Android, cross-platform
- **DevOps Infrastructure** - CI/CD, Terraform, Docker, automazione
- **E molto altro...** - Puoi definire qualsiasi dominio personalizzato!

## Guida Passo-Passo

### 1. Avvio dell'Applicazione

```bash
python3 rag_generator.py
```

L'applicazione si avvia con la finestra principale (800x700px) che include:

- **Configuration Panel** - Impostazioni base (record massimi, delay, URL modelli)
- **Current RAG Configuration** - Visualizzazione configurazione corrente con indicatore di stato
- **Output Format** - Opzione per generare HTML invece di JSON
- **Start/Stop/Refresh/Open Folder** - Controlli principali
- **🦾 RAG Config** - Pulsante per la configurazione avanzata RAG

### 2. Configurazione Base

Nella finestra principale, imposta:
- **Max Records**: 1000 (numero di record da generare)
- **Max Failures**: 3 (soglia di fallimenti prima dello stop)
- **Delay (s)**: 1.0 (ritardo in secondi tra le generazioni)
- **Model X/Y URLs**: I tuoi endpoint LLM

### 3. Configurazione Avanzata RAG

Clicca il pulsante **🦾 RAG Config** per aprire la finestra di personalizzazione:

#### Parametri Configurabili

| Parametro | Default | Esempi | Descrizione |
|-----------|---------|--------|-------------|
| **Domain/Technology** | PHP 8 and HTML5 | 'Python and Machine Learning', 'JavaScript and React' | Dominio tecnologico del problema |
| **Expert Level** | senior architect | 'ML engineer', 'principal engineer', 'DevOps engineer' | Rangolo dell'esperto |
| **Focus/Specialization** | security and performance | 'AI/ML integration', 'cross-platform compatibility' | Area di specializzazione |
| **Constraint Type** | proprietary library constraint | 'ML pipeline constraint', 'framework constraint' | Vincolo richiesto nei problemi |
| **Target Languages** | PHP and/or HTML | 'Python', 'Java and SQL', 'Bash scripting' | Tecnologie/language target |

### 4. Preset Preconfigurati

Clicca **"Load Preset"** per accedere a 7 preset pronti all'uso:

#### Preset Disponibili

| Preset | Domain | Focus | Vincoli | Languages |
|--------|--------|-------|---------|-----------|
| 🟪 **PHP/HTML Security** | PHP 8 and HTML5 | Security and performance | Library constraint | PHP/HTML |
| 🔷 **Python ML Integration** | Python and ML | AI/ML integration | ML pipeline constraint | Python |
| 🟨 **JavaScript Modern Stack** | JavaScript | Performance and UX | Framework constraint | JavaScript/TypeScript |
| 🟦 **Java Enterprise** | Java Enterprise | Scalability | Enterprise pattern | Java and SQL |
| 🟩 **Mobile Development** | Mobile Apps | Cross-platform | Platform constraint | React Native/Swift/Kotlin |
| 🟥 **DevOps Infrastructure** | DevOps and CI/CD | Automation | Infrastructure as code | Bash scripting |
| 🍳 **Cucina e Ricette** | Cucina e Ricette Italiane | Ricette tradizionali | Vincolo culinario | Ricette e tecniche |

### 5. Creazione Preset Personalizzato

Per creare un nuovo preset personalizzato:

1. Compila manualmente i campi nella finestra RAG Config
2. Clicca "Save Configuration"
3. **Esempio pratico**: Per generare dati di Data Science

```
Domain: Python and Data Science
Expert Level: senior data scientist  
Focus: Statistical analysis and visualization
Constraint: statistical model requirement (e.g., "use the `pipeline.fit_transform()` method")
Languages: Python with pandas, scikit-learn, and matplotlib
```

### 6. Configurazione Output Format

Nella finestra principale, nella sezione **"Output Format"**:
- **Web Format OFF** (default): Genera file JSON strutturati per training
- **Web Format ON**: Genera pagine HTML complete, moderne e SEO-friendly

Quando Web Format è attivo:
- Ogni record diventa una pagina HTML completa
- Il titolo viene estratto automaticamente dal requisito
- Il contenuto è formattato professionalmente
- Include meta tags SEO, Open Graph, design responsive
- Pronto per pubblicazione immediata su web

### 7. Avvio della Generazione

1. Configura i parametri nella finestra principale
2. Clicca **"RAG Config"** per personalizzare i prompt (opzionale)
3. Seleziona **"Web Format"** se vuoi generare HTML invece di JSON
4. Clicca **"Start Generation"**
5. Monitora lo stato nel log e nel folder content in tempo reale
6. Usa il pulsante **"Stop"** per interrompere in qualsiasi momento

## Esempi Detagliati di Configurazione

### Esempio 1: Database Security

```yaml
Domain: Database Security with SQL
Expert Level: senior database security specialist
Focus: SQL injection prevention and query optimization
Constraint: database security constraint (e.g., "use prepared statements and SQL user permissions")
Languages: SQL with PostgreSQL, SQLite, and Python integration
```

**Problema tipico generato**:
- "Implementa una stored procedure che controlli i privilegi dell'utente prima di eseguire operazioni DELETE, usando la funzione `check_user_permissions()`."

### Esempio 2: Frontend Performance Optimization

```yaml
Domain: JavaScript and Modern Frontend
Expert Level: UI/UX performance specialist
Focus: page load optimization and rendering performance
Constraint: performance optimization constraint (e.g., "use lazy loading and code splitting techniques")
Languages: JavaScript, TypeScript, HTML, and CSS with Webpack
```

**Problema tipico generato**:
- "Ottimizza il rendering di una grande tabella dati usando virtual scrolling con react-window, implementando memoization per evitare re-render inutili."

### Esempio 3: Cloud-Native DevOps

```yaml
Domain: Cloud Infrastructure and DevOps
Expert Level: senior cloud architect
Focus: decoupling and message queue integration
Constraint: cloud design pattern (e.g., "use event-driven architecture with RabbitMQ")
Languages: Terraform, Docker, Kubernetes, and Python Lambda functions
```

**Problema tipico generato**:
- "Progetta un sistema di notifiche asincrono per un e-commerce usando SNS/SQS di AWS, assicurando l'idempotenza dei messaggi."

### Esempio 4: Cucina e Ricette

```yaml
Domain: Cucina e Ricette Italiane
Expert Level: chef esperto e food writer
Focus: ricette tradizionali e tecniche culinarie
Constraint: vincolo culinario specifico (es. "usa solo ingredienti freschi di stagione" o "seguire il metodo tradizionale")
Languages: Ricette, tecniche culinarie e descrizioni gastronomiche
```

**Problema tipico generato**:
- "Crea una ricetta per la pasta all'amatriciana seguendo la tradizione laziale, utilizzando solo guanciale di qualità DOP e pomodoro San Marzano."

## Struttura dei Prompt Configurabili

### System Prompt per Model X (Planner)

```
Sei un [rag_skill_level] specializzato in [rag_domain], focalizzato su [rag_focus].
Genera un requisito di coding specifico (l'Intent) in formato JSON strict.
L'Intent deve riguardare l'interazione tra [rag_languages] e deve includere almeno un [rag_constraint].

Rispondi SOLO con un JSON in questo formato:
{
  "raw_intent": "...",
  "tags": [...]
}
```

### User Prompt per Model X

```
Genera un nuovo requisito di coding per [rag_languages] con focus su [rag_focus].
```

## Output degli Esempi Reali

### Esempio 1: Python ML

```json
{
  "raw_intent": "Implement a pipeline for feature engineering and cross-validation, using custom custom scaler `StandardScaler2D` with early stopping.",
  "tags": ["python", "ml", "pipeline", "cross-validation"],
  "code_snippet": "import numpy as np\nfrom sklearn.base import BaseEstimator, TransformerMixin\n# Complete solution...",
  "description": "This code implements a custom ML pipeline with feature scaling and cross-validation...",
  "generated_at": "2025-12-23T16:30:15.571181"
}
```

### Esempio 2: React Performance

```json
{
  "raw_intent": "Optimize a React component rendering large data tables using useMemo and useCallback, implementing infinite scroll with the Intersection Observer API.",
  "tags": ["javascript", "react", "performance", "optimization"],
  "code_snippet": "import React, { useState, useEffect, useMemo, useCallback } from 'react';\n// Complete React component...",
  "description": "This React component implements performance optimizations...",
  "generated_at": "2025-12-23T16:35:22.123456"
}
```

## Best Practices per la Configurazione

### 🔍 Focus sulla Qualità

1. **Scegli domini specifici**: Evita "programmazione" troppo generico
   - ❌ Male: "programmazione software"
   - ✅ Bene: "Python data engineering con Apache Airflow"

2. **Definisci skill level realistici**:
   - junior developer → senior architect → principal engineer → tech lead

3. **Specifica vincoli chiari**:
   - ❌ Male: "usa una libreria"
   - ✅ Bene: "mandatory library constraint (e.g., 'use the `Redux Toolkit` for state management')"

4. **Mantieni la coerenza**:
   - Assicurati che Domain/Languages/Focus siano allineati

### 🎯 Esempi di Configurazione Efficace

#### Configurazione per Blockchain

```yaml
Domain: Blockchain and Smart Contracts
Expert Level: blockchain security architect
Focus: smart contract security and gas optimization
Constraint: security pattern (e.g., "use the require() statement for input validation")
Languages: Solidity with Hardhat testing framework
```

#### Configurazione per IoT

```yaml
Domain: Embedded Systems and IoT
Expert Level: senior firmware engineer
Focus: low-power optimization and real-time processing
Constraint: resource constraint (e.g., "use FreeRTOS tasks with 8KB RAM limit")
Languages: C/C++ for embedded systems and Python for device management
```

#### Configurazione per Game Development

```yaml
Domain: Game Development and Unity
Expert Level: senior game developer
Focus: rendering performance and user experience
Constraint: game design pattern (e.g., "use the Object Pool pattern for bullet management")
Languages: Unity C# with shader programming
```

## Troubleshooting

### Problemi Comuni

**🔴 L'LLM non genera contenuti di qualità**
- Verifica la coerenza tra Domain, Focus e Constraints
- Usa constrainst specifici anziché generici
- Prova a cambiare skill level (es. da "developer" a "architect")

**🔴 I contenuti non sono abbastanza vari**
- Modifica periodicamente il focus area
- Alterna tra differenti constraint types
- Usa preset diversi per generare dataset eterogenei

**🔴 Errori di parsing JSON**
- Assicurati che i constraints siano ben formattati
- Controlla che le virgolette non interagiscano con il formato JSON

## Domande Frequenti (FAQ)

### ❓ Posso salvare i miei preset personalizzati?
Sì! La configurazione viene mantenuta durante la sessione e puoi trasferirla manualmente alla prossima esecuzione.

### ❓ Come posso condividere la mia configurazione con altri?
Tutte le configurazioni sono memorizzate nell'oggetto `config.rag_*`. Puoi salvarle in un file JSON per condividerle.

### ❓ Quali domini funzionano meglio?
Tutti i domini con sufficiente contenuto tecnico funzionano bene. Limitati solo dalla tua immaginazione!

### ❓ Posso generare dati in altre lingue (inglese, spagnolo, etc.)?
Sì! Modifica i prompt in `call_model_x()` e `call_model_y()` per cambiare lingua.

### ❓ Come faccio a testare una nuova configurazione?
Usa "Max Records: 5" per un test rapido, controlla i risultati, e poi scala a 1000+ record.

## Link Utili

- [README.md](./README.md) - Panoramica completa del progetto
- [project_showcase.html](./project_showcase.html) - Pagina web per il sito IA
- [GitHub Repository](https://github.com/vittoriomargherita/RAG_Data_Generator) - Source code completo

---

**🎉 Hai creato la tua prima configurazione personalizzata? Condividi la tua esperienza!**