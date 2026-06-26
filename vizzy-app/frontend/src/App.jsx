import { useState } from 'react'
import UploadPanel from './components/UploadPanel'
import AutoMode from './components/AutoMode'
import PilotMode from './components/PilotMode'
import styles from './App.module.css'

const TABS = [
  { id: 'upload', label: '📤 Upload' },
  { id: 'auto', label: '✦ Auto Mode' },
  { id: 'pilot', label: '🧭 Pilot Mode' },
]

export default function App() {
  const [tab, setTab] = useState('upload')
  const [uploadedDoc, setUploadedDoc] = useState(null)

  function handleUploaded(doc) {
    setUploadedDoc(doc)
    setTab('auto')
  }

  return (
    <div className={styles.app}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <div className={styles.logo}>
          <span className={styles.logoMark}>✦</span>
          <span className={styles.logoText}>Vizzy</span>
        </div>

        <nav className={styles.nav}>
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`${styles.navBtn} ${tab === t.id ? styles.active : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        {uploadedDoc && (
          <div className={styles.docStatus}>
            <p className={styles.statusLabel}>Active document</p>
            <p className={styles.statusName}>{uploadedDoc.filename}</p>
            <p className={styles.statusMeta}>{uploadedDoc.total_chunks} chunks indexed</p>
            <button
              className={styles.changeBtn}
              onClick={() => { setUploadedDoc(null); setTab('upload') }}
            >
              Change file
            </button>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className={styles.main}>
        {tab === 'upload' && (
          <UploadPanel onUploaded={handleUploaded} />
        )}
        {tab === 'auto' && (
          <AutoMode uploadedDoc={uploadedDoc} />
        )}
        {tab === 'pilot' && (
          <PilotMode uploadedDoc={uploadedDoc} />
        )}
      </main>
    </div>
  )
}
