
import React from 'react';

interface CodeViewerProps {
  code: string;
  language?: string;
}

const CodeViewer = ({ code, language = 'javascript' }: CodeViewerProps) => {
  // In a real application, we would use a library like Prism.js or highlight.js
  // for proper syntax highlighting
  
  return (
    <div className="code-viewer">
      <pre>
        <code>
          {code}
        </code>
      </pre>
    </div>
  );
};

export default CodeViewer;
