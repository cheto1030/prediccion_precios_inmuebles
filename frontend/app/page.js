"use client";

import { useMemo, useState } from "react";

export default function Home() {
  // URL del backend (local por ahora)
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://prediccion-precios-inmuebles.onrender.com";

  // Estado del formulario (solo 8 campos clave)
  const [form, setForm] = useState({
    OverallQual: 7,
    GrLivArea: 1500,
    TotalBsmtSF: 800,
    YearBuilt: 2000,
    Neighborhood: "CollgCr",
    GarageCars: 2,
    FullBath: 2,
    BedroomAbvGr: 3,
  });

  // Estado de la predicción
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [realPrice, setRealPrice] = useState("");
  const [fbMsg, setFbMsg] = useState("");


  // Formateador de precio (estilo España)
  const formatPrice = useMemo(() => {
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 2,
    });
  }, []);

  // Manejar cambios en inputs
  function handleChange(e) {
    const { name, value } = e.target;

    // Convertimos a número los campos numéricos
    const numericFields = [
      "OverallQual",
      "GrLivArea",
      "TotalBsmtSF",
      "YearBuilt",
      "GarageCars",
      "FullBath",
      "BedroomAbvGr",
    ];

    setForm((prev) => ({
      ...prev,
      [name]: numericFields.includes(name) ? Number(value) : value,
    }));
  }

  // Llamar a /predict
  async function handlePredict() {
    setLoading(true);
    setErrorMsg("");
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ features: form }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err?.detail || "Error desconocido en /predict");
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  }

// Enviar feedback al backend (opcional)
async function handleFeedback() {
  setFbMsg("");

  // Solo se puede enviar feedback si ya existe una predicción
  if (!result) {
    setFbMsg("Primero realiza una predicción antes de enviar feedback.");
    return;
  }

  // Validación: para guardar feedback sí necesitamos un precio real válido
  const priceNum = Number(realPrice);
  if (!priceNum || priceNum <= 0) {
    setFbMsg("Introduce un precio real válido (> 0) para enviar feedback.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        features: form,
        sale_price_real: priceNum,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err?.detail || "Error desconocido en /feedback");
    }

    const data = await res.json();
    setFbMsg(`✅ Feedback enviado. ID guardado: ${data.row_id}`);
  } catch (err) {
    setFbMsg(`❌ Error enviando feedback: ${err.message}`);
  }
}

  return (
    <main style={{ maxWidth: 800, margin: "40px auto", padding: 16, fontFamily: "Arial" }}>
      <h1 style={{ fontSize: 28, marginBottom: 10 }}>
        Predicción de precios de vivienda
      </h1>

      <p style={{ marginBottom: 20, color: "#444" }}>
        Introduce algunas características básicas de la vivienda. El servidor completará el resto
        automáticamente con valores por defecto basados en el dataset de entrenamiento.
      </p>

      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "1fr 1fr" }}>
        {/* Calidad general */}
        <label>
          Calidad general (1–10)
          <input
            type="number"
            name="OverallQual"
            min="1"
            max="10"
            value={form.OverallQual}
            onChange={handleChange}
            style={{ width: "100%", padding: 8, marginTop: 6 }}
          />
        </label>

        {/* Superficie habitable */}
        <label>
          Superficie habitable (ft²)
          <input
            type="number"
            name="GrLivArea"
            value={form.GrLivArea}
            onChange={handleChange}
            style={{ width: "100%", padding: 8, marginTop: 6 }}
          />
        </label>

        {/* Superficie sótano */}
        <label>
          Superficie sótano (ft²)
          <input
            type="number"
            name="TotalBsmtSF"
            value={form.TotalBsmtSF}
            onChange={handleChange}
            style={{ width: "100%", padding: 8, marginTop: 6 }}
          />
        </label>

        {/* Año */}
        <label>
          Año de construcción
          <input
            type="number"
            name="YearBuilt"
            value={form.YearBuilt}
            onChange={handleChange}
            style={{ width: "100%", padding: 8, marginTop: 6 }}
          />
        </label>

        {/* Barrio */}
        <label>
          Barrio
          <select
            name="Neighborhood"
            value={form.Neighborhood}
            onChange={handleChange}
            style={{ width: "100%", padding: 8, marginTop: 6 }}
          >
            <option value="CollgCr">CollgCr</option>
            <option value="NAmes">NAmes</option>
            <option value="OldTown">OldTown</option>
            <option value="Edwards">Edwards</option>
            <option value="Somerst">Somerst</option>
            <option value="NridgHt">NridgHt</option>
          </select>
        </label>

        {/* Garaje */}
        <label>
          Plazas de garaje
          <input
            type="number"
            name="GarageCars"
            value={form.GarageCars}
            onChange={handleChange}
            style={{ width: "100%", padding: 8, marginTop: 6 }}
          />
        </label>

        {/* Baños */}
        <label>
          Baños completos
          <input
            type="number"
            name="FullBath"
            value={form.FullBath}
            onChange={handleChange}
            style={{ width: "100%", padding: 8, marginTop: 6 }}
          />
        </label>

        {/* Dormitorios */}
        <label>
          Dormitorios
          <input
            type="number"
            name="BedroomAbvGr"
            value={form.BedroomAbvGr}
            onChange={handleChange}
            style={{ width: "100%", padding: 8, marginTop: 6 }}
          />
        </label>
      </div>

      <button
        onClick={handlePredict}
        disabled={loading}
        style={{
          marginTop: 18,
          padding: "10px 14px",
          fontSize: 16,
          cursor: "pointer",
        }}
      >
        {loading ? "Calculando..." : "Predecir precio"}
      </button>

      {errorMsg && (
        <div style={{ marginTop: 16, color: "crimson" }}>
          <b>Error:</b> {errorMsg}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 20, padding: 14, border: "1px solid #ddd", borderRadius: 8 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>Resultado</h2>
          <p style={{ marginTop: 10 }}>
            <b>Precio estimado:</b>{" "}
            {formatPrice.format(result.sale_price)}
          </p>
          <p style={{ marginTop: 6, color: "#555" }}>
            ID de predicción: {result.prediction_id}
          </p>
        </div>
      )}

      {result && (
        <div style={{ marginTop: 14, padding: 14, border: "1px solid #eee", borderRadius: 8 }}>
          <h3 style={{ margin: 0, fontSize: 16 }}>Feedback (opcional)</h3>

          <p style={{ marginTop: 8, color: "#555" }}>
            Si más adelante conoces el precio real de venta, puedes enviarlo para guardar un nuevo
            ejemplo etiquetado. Esto permite mejorar el modelo en futuras versiones mediante reentrenamiento.
          </p>

          <label style={{ display: "block", marginTop: 10 }}>
            Precio real de venta (€)
            <input
              type="number"
              value={realPrice}
              onChange={(e) => setRealPrice(e.target.value)}
              style={{ width: "100%", padding: 8, marginTop: 6 }}
              placeholder="Ej: 210000"
            />
          </label>

          <button
            onClick={handleFeedback}
            style={{ marginTop: 12, padding: "10px 14px", cursor: "pointer" }}
          >
            Enviar feedback
          </button>

          {fbMsg && (
            <div style={{ marginTop: 10 }}>
              {fbMsg}
            </div>
          )}
        </div>
      )}
    </main>
  );
}
