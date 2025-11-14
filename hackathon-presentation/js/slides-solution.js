export const solutionSlides = [
  {
    title: "Problem Statement",
    render: () => `
      <p>
        Write your problem in 1–2 killer sentences.<br/><br/>
        <strong>Template:</strong><br/>
        “We help <em>&lt;who&gt;</em> do <em>&lt;what&gt;</em> so that <em>&lt;impact&gt;</em>.”
      </p>
    `
  },
  {
    title: "Our Solution",
    render: () => `
      <p>
        What did you build?<br/><br/>
        Explain the core flow: what users see first, what they do, and the main value they get.
      </p>
    `
  },
  {
    title: "Demo Time",
    render: () => `
      <p>
        This slide is your cue to jump into the live product.<br/><br/>
        Show a real user journey, not every button and config screen.
      </p>
    `
  },
    {
    title: "Tech Stack",
    render: () => `
      <ul class="tech-list">
        <li><strong>Frontend:</strong> (e.g. React, Vite, plain HTML/JS)</li>
        <li><strong>Backend:</strong> (e.g. Node.js, Python, Firebase)</li>
        <li><strong>APIs / Integrations:</strong> (e.g. OpenAI, Stripe, Maps)</li>
        <li><strong>Database / Storage:</strong> (e.g. PostgreSQL, MongoDB, Supabase)</li>
        <li><strong>Dev Tools:</strong> (e.g. GitHub, Docker, Postman)</li>
      </ul>
    `
  }
];
