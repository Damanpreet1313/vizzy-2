import { useState } from 'react'
import { runAutoMode } from '../api'
import ReaderMode from './ReaderMode'
import styles from './AutoMode.module.css'

export default function AutoMode({ uploadedDoc }) {
  const [frames, setFrames] = useState(5)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [collection, setCollection] = useState([])
  const [activeFrame, setActiveFrame] = useState(null)
  const [readerOpen, setReaderOpen] = useState(false)
  const [readerStart, setReaderStart] = useState(0)

  async function handleRun() {
    if (!uploadedDoc) return
    setError('')
    setLoading(true)
    setCollection([])
    setActiveFrame(null)
    try {
      const result = await runAutoMode(uploadedDoc.filePath, frames)
      setCollection(result.collection)
      if (result.collection.length > 0) setActiveFrame(result.collection[0])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function openReader(startIndex = 0) {
    setReaderStart(startIndex)
    setReaderOpen(true)
  }

  return (
    <>
      {/* ── Fullscreen reader overlay ── */}
      {readerOpen && (
        <ReaderMode
          collection={collection}
          startIndex={readerStart}
          onClose={() => setReaderOpen(false)}
        />
      )}

      <div className={styles.wrap}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>Auto Mode</h2>
            <p className={styles.sub}>Vizzy reads your document and builds a cinematic storyboard automatically.</p>
          </div>
        </div>

        {!uploadedDoc ? (
          <div className={styles.empty}>
            <span className={styles.emptyIcon}>📂</span>
            <p>Upload a document first to use Auto Mode.</p>
          </div>
        ) : (
          <div className={styles.controls}>
            <div className={styles.docBadge}>
              <span className={styles.docIcon}>📄</span>
              <span className={styles.docName}>{uploadedDoc.filename}</span>
              <span className={styles.docChunks}>{uploadedDoc.total_chunks} chunks</span>
            </div>

            <div className={styles.row}>
              <label className={styles.label}>
                Frames to generate
                <span className={styles.frameCount}>{frames}</span>
              </label>
              <input
                type="range"
                min={1}
                max={20}
                value={frames}
                onChange={(e) => setFrames(Number(e.target.value))}
                className={styles.slider}
              />
              <div className={styles.sliderLabels}><span>1</span><span>20</span></div>
            </div>

            <button
              className={styles.runBtn}
              onClick={handleRun}
              disabled={loading}
            >
              {loading ? (
                <><span className={styles.spinner} /> Generating storyboard…</>
              ) : '✦ Generate Storyboard'}
            </button>

            {error && <p className={styles.error}>⚠ {error}</p>}
          </div>
        )}

        {collection.length > 0 && (
          <div className={styles.storyboard}>
            {/* Start Reading banner */}
            <div className={styles.readBanner}>
              <div className={styles.readBannerText}>
                <span className={styles.readBannerTitle}>✦ {collection.length} frames ready</span>
                <span className={styles.readBannerSub}>Step through each visual as you read</span>
              </div>
              <button className={styles.startReadingBtn} onClick={() => openReader(0)}>
                ▶ Start Reading
              </button>
            </div>

            {/* Main viewer (gallery preview) */}
            {activeFrame && (
              <div className={styles.viewer}>
                <div className={styles.imageWrap}>
                  <img
                    src={activeFrame.image_url}
                    alt={`Frame ${activeFrame.frame_index + 1}`}
                    className={styles.mainImage}
                    loading="lazy"
                  />
                  <div className={styles.frameBadge}>
                    Frame {activeFrame.frame_index + 1} / {collection.length}
                  </div>
                  {/* Click image to open reader at this frame */}
                  <button
                    className={styles.openReaderOverlay}
                    onClick={() => openReader(activeFrame.frame_index)}
                    aria-label="Open in reader"
                  >
                    <span className={styles.openReaderIcon}>⛶</span>
                    <span>Open in reader</span>
                  </button>
                </div>
                <div className={styles.frameInfo}>
                  {activeFrame.quote && (
                    <blockquote className={styles.quote}>"{activeFrame.quote}"</blockquote>
                  )}
                  {activeFrame.text_summary && (
                    <p className={styles.summary}>{activeFrame.text_summary}</p>
                  )}
                </div>
              </div>
            )}

            {/* Thumbnail strip */}
            <div className={styles.strip}>
              {collection.map((frame) => (
                <button
                  key={frame.frame_index}
                  className={`${styles.thumb} ${activeFrame?.frame_index === frame.frame_index ? styles.thumbActive : ''}`}
                  onClick={() => setActiveFrame(frame)}
                >
                  <img
                    src={frame.image_url}
                    alt={`Frame ${frame.frame_index + 1}`}
                    className={styles.thumbImg}
                    loading="lazy"
                  />
                  <span className={styles.thumbLabel}>{frame.frame_index + 1}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  )
}
