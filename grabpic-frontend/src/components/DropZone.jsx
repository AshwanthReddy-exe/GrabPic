import { useState, useRef, useMemo } from "react";
import clsx from "clsx";

/**
 * DropZone — Drag-and-drop file upload area with previews.
 */
export default function DropZone({
  label = "Upload Photos",
  sublabel,
  accept = "image/*",
  multiple = true,
  maxFiles,
  onFiles,
  className,
}) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const processFiles = (fileList) => {
    let files = Array.from(fileList);
    if (files.length === 0) return;
    if (maxFiles && files.length > maxFiles) {
      files = files.slice(0, maxFiles);
    }
    setSelectedFiles(files);
    onFiles?.(files);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    processFiles(e.dataTransfer.files);
  };

  const handleChange = (e) => {
    processFiles(e.target.files);
  };

  const previews = useMemo(() => {
    return selectedFiles.slice(0, 6).map((file) => URL.createObjectURL(file));
  }, [selectedFiles]);

  return (
    <div
      className={clsx("dropzone", dragActive && "dropzone--active", className)}
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleChange}
        style={{ display: "none" }}
      />

      <div className="dropzone__label">{label}</div>
      {sublabel && <div className="dropzone__sublabel">{sublabel}</div>}

      {selectedFiles.length > 0 && (
        <>
          <div className="dropzone__sublabel mt-8">
            {selectedFiles.length} file{selectedFiles.length > 1 ? "s" : ""} selected
          </div>
          {previews.length > 0 && (
            <div className="dropzone__previews">
              {previews.map((src, i) => (
                <img
                  key={i}
                  src={src}
                  alt={`Preview ${i + 1}`}
                  className="dropzone__preview-thumb"
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
