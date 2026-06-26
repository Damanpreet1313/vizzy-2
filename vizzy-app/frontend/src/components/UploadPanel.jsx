import { useState, useRef } from 'react'
import { uploadFile } from '../api'
import styles from './UploadPanel.module.css'

export default function UploadPanel({ onUploaded }) {
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef()

  async function handleFile(file) {
    if (!file) return
    if (!file.name.endsWith('.pdf') && !file.name.endsWith('.txt')) {
      setError('Only PDF or TXT files are supported.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const result = await uploadFile(file)
      onUploaded(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }

  return (
    <div className={styles.wrap}>
      <h2 className={styles.title}>Upload a Document</h2>
      <p className={styles.sub}>Supports PDF and TXT files. Your document will be chunked and indexed for both modes.</p>

      <div
        className={`${styles.dropzone} ${dragging ? styles.active : ''}`}
        onClick={() => inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <div className={styles.icon}>📄</div>
        <p className={styles.dropText}>
          {loading ? 'Uploading & indexing…' : 'Drop your file here or click to browse'}
        </p>
        <p className={styles.hint}>PDF · TXT</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          className={styles.hidden}
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      {loading && (
        <div className={styles.progress}>
          <div className={styles.bar} />
        </div>
      )}

      {error && <p className={styles.error}>⚠ {error}</p>}
    </div>
  )
}
