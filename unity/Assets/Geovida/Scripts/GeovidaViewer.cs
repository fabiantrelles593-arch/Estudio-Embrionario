// Geometría de la Vida (geovida) - visor 4D para Unity.
//
// Lee StreamingAssets/geovida_series.json (lo escribe scripts/export_unity.py) y dibuja, etapa
// por etapa, los vóxeles que la imagen atribuye a un objeto que crece con el vóxel fijo. El color
// es la luz del semáforo de volumen: verde, amarillo o rojo. Solo datos sintéticos.
//
// Uso: escena vacía -> GameObject vacío -> añadir este componente -> Play.
// No usa UnityEngine.Input (funciona con el Input System nuevo): la interacción va por OnGUI.
using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

public class GeovidaViewer : MonoBehaviour
{
    [Serializable] public class Stage
    {
        public int stage; public float tOverH; public int[] dims; public float[] spacing;
        public float volume; public float volumeTrue; public float errVolume; public float p;
        public string light; public int[] betti; public int[] bettiTrue; public int[] voxels;
    }
    [Serializable] public class Series { public string shape; public float trueRate; public Stage[] stages; }
    [Serializable] public class Payload { public string note; public Series[] series; }

    const int BatchSize = 1023;                       // límite de Graphics.DrawMeshInstanced
    Payload data;
    Mesh cube;
    Material material;
    readonly List<Matrix4x4[]> batches = new List<Matrix4x4[]>();
    readonly List<int> batchCounts = new List<int>();
    int shapeIndex, stageIndex;
    float yaw = 30f, pitch = 20f, zoom = 1f, radius = 10f;
    string error;

    void Start()
    {
        string path = Path.Combine(Application.streamingAssetsPath, "geovida_series.json");
        if (!File.Exists(path)) { error = "Falta " + path + ". Ejecuta scripts/export_unity.py."; return; }
        data = JsonUtility.FromJson<Payload>(File.ReadAllText(path));
        if (data == null || data.series == null || data.series.Length == 0) { error = "El JSON no tiene series."; return; }

        GameObject temp = GameObject.CreatePrimitive(PrimitiveType.Cube);
        cube = temp.GetComponent<MeshFilter>().sharedMesh;
        Destroy(temp);

        Shader shader = Shader.Find("Universal Render Pipeline/Lit");
        if (shader == null) shader = Shader.Find("Standard");
        material = new Material(shader) { enableInstancing = true };

        if (Camera.main == null)
        {
            GameObject cam = new GameObject("Main Camera") { tag = "MainCamera" };
            cam.AddComponent<Camera>();
        }
        if (FindObjectOfType<Light>() == null)
        {
            GameObject sun = new GameObject("Sun");
            Light l = sun.AddComponent<Light>();
            l.type = LightType.Directional;
            sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
        }
        Rebuild();
    }

    Stage Current { get { return data.series[shapeIndex].stages[stageIndex]; } }

    static Color LightColor(string light)
    {
        if (light == "verde") return new Color(0.04f, 0.56f, 0.41f);
        if (light == "amarillo") return new Color(0.89f, 0.70f, 0.25f);
        return new Color(0.77f, 0.29f, 0.10f);
    }

    void Rebuild()
    {
        batches.Clear(); batchCounts.Clear();
        Stage s = Current;
        Vector3 size = new Vector3(s.spacing[0], s.spacing[1], s.spacing[2]);
        Vector3 centre = new Vector3((s.dims[0] - 1) * 0.5f * size.x, (s.dims[1] - 1) * 0.5f * size.y,
                                     (s.dims[2] - 1) * 0.5f * size.z);
        Vector3 scale = size * 0.9f;
        int n = s.voxels.Length / 3;
        Matrix4x4[] batch = null; int filled = 0;
        for (int v = 0; v < n; v++)
        {
            if (batch == null) { batch = new Matrix4x4[BatchSize]; filled = 0; }
            Vector3 pos = new Vector3(s.voxels[3 * v] * size.x, s.voxels[3 * v + 1] * size.y,
                                      s.voxels[3 * v + 2] * size.z) - centre;
            batch[filled++] = Matrix4x4.TRS(pos, Quaternion.identity, scale);
            if (filled == BatchSize) { batches.Add(batch); batchCounts.Add(filled); batch = null; }
        }
        if (batch != null && filled > 0) { batches.Add(batch); batchCounts.Add(filled); }

        Color c = LightColor(s.light);
        if (material.HasProperty("_BaseColor")) material.SetColor("_BaseColor", c);
        if (material.HasProperty("_Color")) material.SetColor("_Color", c);
        radius = 0.5f * new Vector3(s.dims[0] * size.x, s.dims[1] * size.y, s.dims[2] * size.z).magnitude;
    }

    void Update()
    {
        if (data == null) return;
        Quaternion rot = Quaternion.Euler(pitch, yaw, 0f);
        Camera cam = Camera.main;
        if (cam != null)
        {
            float dist = Mathf.Max(radius, 2f) * 3.2f * zoom;
            cam.transform.position = rot * new Vector3(0f, 0f, -dist);
            cam.transform.rotation = rot;
            cam.nearClipPlane = dist / 100f;
            cam.farClipPlane = dist * 10f;
        }
        for (int b = 0; b < batches.Count; b++)
            Graphics.DrawMeshInstanced(cube, 0, material, batches[b], batchCounts[b]);
    }

    void OnGUI()
    {
        if (error != null) { GUI.Label(new Rect(10, 10, 900, 60), error); return; }
        if (data == null) return;

        Event e = Event.current;                      // girar y acercar sin UnityEngine.Input
        if (e.type == EventType.MouseDrag && e.mousePosition.x > 330f)
        {
            yaw += e.delta.x * 0.4f;
            pitch = Mathf.Clamp(pitch + e.delta.y * 0.4f, -85f, 85f);
        }
        if (e.type == EventType.ScrollWheel) zoom = Mathf.Clamp(zoom * (1f + e.delta.y * 0.03f), 0.3f, 4f);

        GUILayout.BeginArea(new Rect(10, 10, 310, 420), GUI.skin.box);
        GUILayout.Label("Geometría de la Vida - visor 4D (datos sintéticos)");
        GUILayout.Label("Forma: " + data.series[shapeIndex].shape);
        int newShape = Mathf.RoundToInt(GUILayout.HorizontalSlider(shapeIndex, 0, data.series.Length - 1));
        Stage s = Current;
        GUILayout.Label("Etapa " + s.stage + " - grosor " + s.tOverH.ToString("0.0") + " vóxeles");
        int newStage = Mathf.RoundToInt(GUILayout.HorizontalSlider(stageIndex, 0, data.series[shapeIndex].stages.Length - 1));
        GUILayout.Space(8);
        GUILayout.Label("Semáforo de volumen: " + s.light.ToUpper() + "  (p = " + s.p.ToString("0.00") + ")");
        GUILayout.Label("Error real de volumen: " + (100f * s.errVolume).ToString("+0.0;-0.0") + " %");
        GUILayout.Label("Topología medida: (" + s.betti[0] + ", " + s.betti[1] + ", " + s.betti[2] + ")");
        GUILayout.Label("Topología verdadera: (" + s.bettiTrue[0] + ", " + s.bettiTrue[1] + ", " + s.bettiTrue[2] + ")");
        GUILayout.Space(8);
        GUILayout.Label("La luz se calcula solo con la máscara y el vóxel.\nEl error real se conoce porque la forma es matemática.\nSin uso clínico.");
        GUILayout.Label("Arrastra para girar; rueda para acercar.");
        GUILayout.EndArea();

        if (newShape != shapeIndex || newStage != stageIndex)
        {
            shapeIndex = newShape;
            stageIndex = Mathf.Min(newStage, data.series[shapeIndex].stages.Length - 1);
            Rebuild();
        }
    }
}
