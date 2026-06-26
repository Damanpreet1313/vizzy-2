import { useState, useRef, useEffect } from 'react'
import { runPilotMode } from '../api'
import styles from './PilotMode.module.css'

export default function PilotMode({ uploadedDoc }) {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSend() {
    const q = query.trim()
    if (!q || loading || !uploadedDoc) return
    setQuery('')
    setError('')
    const userMsg = { role: 'user', text: q }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)
    try {
      const result = await runPilotMode(q, uploadedDoc.collection_name)
      const botMsg = {
        role: 'bot',
        text: result.reply,
        imageUrl: result.imageUrl,
      }
      setMessages((prev) => [...prev, botMsg])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <h2 className={styles.title}>Pilot Mode</h2>
        <p className={styles.sub}>Ask Vizzy anything about your document — it will respond and generate a matching visual.</p>
      </div>

      {!uploadedDoc ? (
        <div className={styles.empty}>
          <span className={styles.emptyIcon}>🧭</span>
          <p>Upload a document first to start exploring with Pilot Mode.</p>
        </div>
      ) : (
        <div className={styles.chatWrap}>
          <div className={styles.docBadge}>
            <span>📄</span>
            <span className={styles.docName}>{uploadedDoc.filename}</span>
            <span className={styles.collectionTag}>{uploadedDoc.collection_name}</span>
          </div>

          <div className={styles.messages}>
            {messages.length === 0 && (
              <div className={styles.welcome}>
                <p className={styles.welcomeTitle}>Ask anything about <strong>{uploadedDoc.filename}</strong></p>
                <div className={styles.suggestions}>
                  {['Describe the main character', 'What is the central conflict?', 'Create a visual of the opening scene'].map((s) => (
                    <button key={s} className={styles.suggestion} onClick={() => setQuery(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`${styles.msg} ${msg.role === 'user' ? styles.user : styles.bot}`}>
                {msg.role === 'bot' && (
                  <div className={styles.avatar}>✦</div>
                )}
                <div className={styles.bubble}>
                  <p className={styles.msgText}>{msg.text}</p>
                  {msg.imageUrl && (
                    <div className={styles.generatedImg}>
                      <img src={msg.imageUrl} alt="Generated visualization" loading="lazy" />
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className={`${styles.msg} ${styles.bot}`}>
                <div className={styles.avatar}>✦</div>
                <div className={styles.bubble}>
                  <div className={styles.typing}>
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}

            {error && <p className={styles.error}>⚠ {error}</p>}
            <div ref={bottomRef} />
          </div>

          <div className={styles.inputRow}>
            <textarea
              className={styles.textarea}
              rows={2}
              placeholder="Ask Vizzy about your document…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
            />
            <button
              className={styles.sendBtn}
              onClick={handleSend}
              disabled={loading || !query.trim()}
            >
              {loading ? <span className={styles.spinner} /> : '↑'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
