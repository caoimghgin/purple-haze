import { useState, useMemo } from "react";
import { generateRows, type InterpolationRow, type SwatchData } from "./colorEngine";
import "./App.css";

function Swatch({ swatch }: { swatch: SwatchData }) {
  const textColor = swatch.lightness > 55 ? "#000" : "#fff";
  return (
    <div
      className="swatch"
      style={{ backgroundColor: swatch.hex, color: textColor }}
      title={`${swatch.hex}\nL* ${swatch.lightness}`}
    >
      <span className="swatch-hex">{swatch.hex}</span>
    </div>
  );
}

function SwatchRow({ row }: { row: InterpolationRow }) {
  return (
    <div className="swatch-row">
      <div className="row-label">
        <strong>{row.label}</strong>
        <span className="row-description">{row.description}</span>
      </div>
      <div className="row-swatches">
        {row.swatches.map((s, i) => (
          <Swatch key={i} swatch={s} />
        ))}
      </div>
    </div>
  );
}

function App() {
  const [inputColor, setInputColor] = useState("#0044ff");

  const { toWhite, toBlack } = useMemo(
    () => generateRows(inputColor),
    [inputColor]
  );

  return (
    <div className="app">
      <header>
        <h1>Purple Haze</h1>
        <p className="subtitle">
          Why does blue go purple when you fade it to black?
          <br />
          Compare color interpolation across different color spaces.
        </p>
        <div className="color-picker-wrapper">
          <label htmlFor="colorInput">Pick a color</label>
          <div className="picker-row">
            <input
              id="colorInput"
              type="color"
              value={inputColor}
              onChange={(e) => setInputColor(e.target.value)}
            />
            <input
              type="text"
              className="hex-input"
              value={inputColor}
              onChange={(e) => {
                const v = e.target.value;
                if (/^#[0-9a-fA-F]{6}$/.test(v)) setInputColor(v);
              }}
              onBlur={(e) => {
                const v = e.target.value;
                if (/^#[0-9a-fA-F]{6}$/.test(v)) setInputColor(v);
              }}
              maxLength={7}
              spellCheck={false}
            />
          </div>
          <p className="hint">
            Try <button className="preset" onClick={() => setInputColor("#0000ff")}>#0000ff</button>{" "}
            <button className="preset" onClick={() => setInputColor("#0044ff")}>#0044ff</button>{" "}
            <button className="preset" onClick={() => setInputColor("#0088ff")}>#0088ff</button>{" "}
            — blues show the purple shift most dramatically
          </p>
        </div>
      </header>

      <section>
        <h2>Fade to White</h2>
        <div className="rows-container">
          {toWhite.map((row) => (
            <SwatchRow key={row.space} row={row} />
          ))}
        </div>
      </section>

      <section>
        <h2>Fade to Black</h2>
        <div className="rows-container">
          {toBlack.map((row) => (
            <SwatchRow key={row.space} row={row} />
          ))}
        </div>
      </section>

      <footer>
        <p>
          Built with <a href="https://colorjs.io" target="_blank" rel="noopener">colorjs.io</a>.
          The purple hue shift in CIE L*a*b* is a well-known artifact of that color space's
          non-uniform hue linearity. OKLab corrects this.
        </p>
      </footer>
    </div>
  );
}

export default App;
