import { useState, useRef } from "react";

export default function FileUpload({ sessionId, onUploadSuccess }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState("");
  const inputRef = useRef();

  const handleFiles = async (files) => {
    if (!files.length) return;
    setUploading(true);
    setError("");
    setUploadResult(null);

    try {
      const { uploadFile } = await import("../api");
      const result = await uploadFile(files[0], sessionId);
      setUploadResult(result);
      onUploadSuccess(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="upload-section">
      <div
        className={`drop-zone ${dragging ? "dragging" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md,.csv,.json,.xml,.html,.py,.log"
          style={{ display: "none" }}
          onChange={(e) => handleFiles(e.target.files)}
        />
        {uploading ? (
          <div className="upload-status">
            <div className="spinner" />
            <p>Processing document...</p>
          </div>
        ) : (
          <>
            <div className="upload-icon">📄</div>
            <p className="upload-text">Drop a file here or click to upload</p>
            <p className="upload-hint">PDF, DOCX, TXT, MD, CSV and more</p>
          </>
        )}
      </div>

      {error && <div className="error-msg">{error}</div>}

      {uploadResult && (
        <div className="upload-success">
          <strong>✓ {uploadResult.filename}</strong> processed —{" "}
          {uploadResult.num_chunks} chunks indexed ({uploadResult.num_characters.toLocaleString()} chars)
        </div>
      )}
    </div>
  );
}
