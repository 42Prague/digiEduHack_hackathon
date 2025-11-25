export const solutionSlides = [
  {
    title: "Problem Statement",
    render: () => `
      <p>
        Build an AI-powered data intelligence platform that automatically adapts to any data format, enables cross-regional comparisons, and measures intervention impact over time
      </p>
    `
  },
  {
    title: "Our Solution",
    render: () => `
<p>

</p>

<ul style="text-align: left; margin: 0 auto; max-width: 480px;">
  <li>Direct Excel → database import with one-click synchronization</li>
  <li>Unique key tokens for secure, error-free user identification</li>
  <li>Automatic data validation and instant problem alerts</li>
  <li>Preloaded participant details (region, school, subject, etc.)</li>
  <li>Clean, consistent data with no typos or manual cleanup</li>
  <li>Real-time results: comparisons, charts, statistics, and analytics</li>
</ul>
    `
  },
{
  title: "Demo Time",
  render: () => `
    <div style="
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      text-align: center;
    ">

      <video 
        src="./assets/demo.mp4" 
        controls 
        style="
          width: 80%;
          max-width: 900px;
          border-radius: 12px;
          box-shadow: 0 6px 20px rgba(0,0,0,0.35);
        "
      ></video>

      <p style="font-size: 1.15rem; max-width: 70%; line-height:1.6;">
        Watch the core user journey — the part that proves your solution works.
      </p>
    </div>
  `
}
,
    {
    title: "Tech Stack",
    render: () => `
      <ul class="tech-list">
        <li><strong>Frontend:</strong> (e.g. plain HTML/JS)</li>
        <li><strong>Backend:</strong> (e.g. Node.js, Python, NextJS)</li>
        <li><strong>Database / Storage:</strong> (e.g. PostgreSQL, SQLlight)</li>
        <li><strong>Dev Tools:</strong> (e.g. GitHub, Docker)</li>
      </ul>
    `
  }
];
