import React, { useEffect, useRef, useState } from "react";

interface WelcomeSplashProps {
  open: boolean;
  onClose: (doNotShowAgain: boolean) => void;
}

export function WelcomeSplash({ open, onClose }: WelcomeSplashProps) {
  const [doNotShow, setDoNotShow] = useState(false);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      const t = setTimeout(() => closeButtonRef.current?.focus(), 0);
      const onKey = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          onClose(doNotShow);
        }
      };
      window.addEventListener("keydown", onKey);
      return () => {
        clearTimeout(t);
        window.removeEventListener("keydown", onKey);
      };
    }
  }, [open, onClose, doNotShow]);

  if (!open) return null;

  return (
    <div className="modal-overlay active" role="dialog" aria-modal="true" aria-labelledby="welcome-title">
      <div className="modal-container" style={{ maxWidth: 560 }}>
        <div className="modal-header">
          <h3 id="welcome-title" className="modal-title">Welcome</h3>
        </div>
        <div className="modal-body">
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
            <img
              src="/static/images/me_construction.png"
              alt="Walshy in a hard hat"
              style={{ width: 120, height: 120, objectFit: "cover", borderRadius: 16, boxShadow: "0 4px 12px rgba(0,0,0,0.15)", background: "#fff" }}
            />
            <div style={{ width: "100%", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
{`Hello Friend,

Thank you for choosing my app as a possible solution to your EES headache,

I hope you enjoy the app and feel free to look arounf around and let me know if you find anything that looks wierd or buggy.

This calander wil be a masterpice IMO when finished, however, right now tho its not finished. but it will be soon. 

Your friend 



Walshy`}
            </div>
            <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
              <input
                type="checkbox"
                checked={doNotShow}
                onChange={(e) => setDoNotShow(e.target.checked)}
              />
              <span>Do not show again</span>
            </label>
          </div>
        </div>
        <div className="modal-footer">
          <button
            ref={closeButtonRef}
            type="button"
            className="btn btn-primary"
            onClick={() => onClose(doNotShow)}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}


