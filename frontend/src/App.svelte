<script>
  let prompt = "";
  let isSending = false;
  
  let messages = [
    {
      role: 'user',
      content: 'Show top 5 merchants by total spending'
    },
    {
      role: 'ai',
      content: '<b>Analytics Agent:</b><br><br>1. 99 SPEED MART — RM12,580.20<br>2. KFC — RM10,122.40<br>3. MYDIN — RM9,875.30<br>4. WATSONS — RM8,621.90<br>5. AEON — RM7,994.10',
      sql: 'SELECT company_name,\nSUM(total_amount) AS total_spending\nFROM receipts\nGROUP BY company_name\nORDER BY total_spending DESC\nLIMIT 5;'
    }
  ];

  let traceItems = [
    "🧠 Agent Manager received request",
    "📊 Analytics Agent selected",
    "⚙️ SQL generated",
    "🗄️ Query executed",
    "📈 Insights generated",
    "✅ Response delivered"
  ];

  let agentStatus = [
    { name: 'Agent Manager', active: true },
    { name: 'Analytics Agent', active: true },
    { name: 'SQL Generator', active: true },
    { name: 'Supabase Connector', active: true },
  ];

  async function sendMessage() {
    if (!prompt.trim()) return;
    
    messages = [...messages, { role: 'user', content: prompt }];
    let currentPrompt = prompt;
    prompt = "";
    isSending = true;
    
    traceItems = ["🧠 Agent Manager received request"];
    agentStatus = agentStatus.map(a => ({...a, active: false}));
    agentStatus[0].active = true;

    try {
      // Pointing to the live HuggingFace backend!
      const API_URL = import.meta.env.VITE_API_URL || "https://arehhham-carrera-ai-backend.hf.space";
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: currentPrompt })
      });
      const data = await res.json();
      
      traceItems = [
        "🧠 Agent Manager received request",
        "📊 Analytics Agent selected", 
        "⚙️ SQL generated",
        "🗄️ Query executed",
        "✅ Response delivered"
      ];
      agentStatus = agentStatus.map(a => ({...a, active: true}));
      
      let display_content = data.answer;
      // Strip SQL fences from text if present
      if (display_content.includes("```sql")) {
         display_content = display_content.replace(/```sql[\s\S]*?```/g, '');
      }
      
      let sql = data.sql_query || "-- No SQL Generated";
      
      messages = [...messages, { role: 'ai', content: display_content, sql }];
    } catch (e) {
      messages = [...messages, { role: 'ai', content: "Error connecting to backend.", sql: "" }];
    }
    isSending = false;
  }
</script>

<main>
  <div class="header doodle">
    <div class="title">🤖 Carrera AI</div>
    <div class="subtitle">
      Multi-Agent Platform • Orchestrator • Text-to-SQL • RAG • Analytics
    </div>
  </div>

  <div class="metrics">
    <div class="metric doodle">
      <div>F1 SCORE</div>
      <div class="metric-value">91.64%</div>
    </div>
    <div class="metric doodle">
      <div>JSON COMPLIANCE</div>
      <div class="metric-value">100%</div>
    </div>
    <div class="metric doodle">
      <div>RECEIPTS</div>
      <div class="metric-value">626</div>
    </div>
    <div class="metric doodle">
      <div>AVG TIME</div>
      <div class="metric-value">4.16s</div>
    </div>
  </div>

  <div class="layout">
    <div class="left-col">
      <div class="panel doodle">
        <div class="panel-title">💬 Ask The Agent</div>
        <div class="chatbox">
          {#each messages as msg}
            {#if msg.role === 'user'}
              <div class="user">{msg.content}</div>
            {:else}
              <div class="ai">
                {@html msg.content}
              </div>
              {#if msg.sql}
                <div class="sql">{msg.sql}</div>
              {/if}
            {/if}
          {/each}
          
          {#if isSending}
             <div class="ai" style="opacity: 0.6">Thinking...</div>
          {/if}
        </div>
        
        <form on:submit|preventDefault={sendMessage} class="chat-input-container">
          <input type="text" bind:value={prompt} placeholder="Ask about your receipts..." disabled={isSending} />
          <button type="submit" disabled={isSending}>Send</button>
        </form>
      </div>

      <br>

      <div class="panel doodle">
        <div class="panel-title">⚡ Agent Execution Trace</div>
        {#each traceItems as trace}
           <div class="trace-item">{trace}</div>
        {/each}
      </div>
    </div>

    <div class="right-col">
      <div class="panel doodle">
        <div class="panel-title">🤖 Live Agent Status</div>
        {#each agentStatus as agent}
          <div class="agent">
            <span>{agent.name}</span>
            <span><span class="dot" style="background: {agent.active ? '#33cc66' : '#ccc'}"></span> {agent.active ? 'Active' : 'Idle'}</span>
          </div>
        {/each}
      </div>

      <br>

      <div class="panel doodle">
        <div class="panel-title">🎨 Agent Orchestration</div>
        <div class="graph">
          <div class="node manager">Agent Manager</div>
          <br>⬇<br>
          <div class="node analytics">Analytics Agent</div>
          <br>⬇<br>
          <div class="node">SQL Generator</div>
          <br>⬇<br>
          <div class="node supabase">Supabase</div>
          <br>⬇<br>
          <div class="node">Insight Engine</div>
        </div>
      </div>
    </div>
  </div>

  <div class="footer doodle">
    ✨ Doodle Theme • Red + Yellow + Blue + White • Vercel Ready
  </div>
</main>

<style>
@import url('https://fonts.googleapis.com/css2?family=Patrick+Hand&family=Nunito:wght@400;700;900&display=swap');

:global(:root) {
  --red: #ff5b5b;
  --yellow: #ffd93d;
  --blue: #4d96ff;
  --white: #ffffff;
  --bg: #faf7f2;
  --ink: #1f1f1f;
}

:global(*) {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:global(body) {
  background: var(--bg);
  font-family: 'Nunito', sans-serif;
  color: var(--ink);
  padding: 24px;
  background-image:
    radial-gradient(circle at 10% 20%, rgba(255,217,61,.25) 0 120px, transparent 121px),
    radial-gradient(circle at 90% 10%, rgba(77,150,255,.18) 0 140px, transparent 141px),
    radial-gradient(circle at 85% 80%, rgba(255,91,91,.18) 0 140px, transparent 141px);
  background-attachment: fixed;
}

.doodle {
  border: 4px solid var(--ink);
  border-radius: 28px;
  box-shadow: 8px 8px 0 var(--ink);
}

.header {
  background: white;
  padding: 28px;
  margin-bottom: 22px;
}

.title {
  font-family: 'Patrick Hand', cursive;
  font-size: 54px;
  line-height: 1;
}

.subtitle {
  margin-top: 10px;
  font-size: 18px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-bottom: 22px;
}

.metric {
  padding: 22px;
  background: white;
}

.metric:nth-child(1) { background: var(--yellow); }
.metric:nth-child(2) { background: var(--blue); color: white; }
.metric:nth-child(3) { background: var(--red); color: white; }
.metric:nth-child(4) { background: white; }

.metric-value {
  font-size: 38px;
  font-weight: 900;
}

.layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 22px;
}

.panel {
  background: white;
  padding: 24px;
}

.panel-title {
  font-family: 'Patrick Hand', cursive;
  font-size: 34px;
  margin-bottom: 16px;
}

.chatbox {
  background: #fffef9;
  padding: 18px;
  border: 3px dashed var(--ink);
  border-radius: 20px;
  max-height: 500px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.user {
  background: var(--blue);
  color: white;
  padding: 14px;
  border-radius: 18px 18px 4px 18px;
  margin-bottom: 16px;
  align-self: flex-end;
  text-align: right;
}

.ai {
  background: var(--yellow);
  padding: 16px;
  border-radius: 18px 18px 18px 4px;
  margin-bottom: 10px;
}

.sql {
  margin-top: 5px;
  margin-bottom: 16px;
  background: #f5f5f5;
  padding: 16px;
  border-radius: 16px;
  border: 3px solid var(--ink);
  font-family: monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.chat-input-container {
  display: flex;
  gap: 10px;
}

.chat-input-container input {
  flex-grow: 1;
  padding: 12px 18px;
  border: 3px solid var(--ink);
  border-radius: 20px;
  font-size: 16px;
  font-family: 'Nunito', sans-serif;
  box-shadow: 4px 4px 0 var(--blue);
  outline: none;
}

.chat-input-container button {
  padding: 12px 24px;
  border: 3px solid var(--ink);
  border-radius: 20px;
  background: var(--red);
  color: white;
  font-weight: bold;
  font-size: 16px;
  cursor: pointer;
  box-shadow: 4px 4px 0 var(--ink);
  transition: all 0.2s;
}

.chat-input-container button:active {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 var(--ink);
}

.trace-item {
  padding: 12px;
  margin: 10px 0;
  background: #fff;
  border-left: 8px solid var(--blue);
  border-radius: 10px;
}

.agent {
  display: flex;
  justify-content: space-between;
  margin: 10px 0;
  padding: 12px;
  background: #fffef8;
  border: 3px solid var(--ink);
  border-radius: 14px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
  transition: background-color 0.3s;
}

.graph {
  text-align: center;
  line-height: 2.4;
}

.node {
  display: inline-block;
  padding: 10px 18px;
  background: white;
  border: 3px solid var(--ink);
  border-radius: 999px;
  font-weight: 800;
}

.manager { background: var(--red); color: white; }
.analytics { background: var(--yellow); }
.supabase { background: var(--blue); color: white; }

.footer {
  margin-top: 22px;
  padding: 20px;
  background: white;
  text-align: center;
  font-weight: 700;
}

@media(max-width: 1000px) {
  .metrics, .layout {
    grid-template-columns: 1fr;
  }
}
</style>
