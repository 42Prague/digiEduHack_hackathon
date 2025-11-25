export const closingSlides = [
  {
    title: "Future Improvements",
    render: () => `
      <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 1.2rem;
      ">
        <img 
          src="./assets/prompt.png" 
          style="
            width: 60%;
            max-width: 420px;
            height: auto;
            border-radius: 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
          "
        />

        <p>
        In the future, we want the system to manage question blocks in a much more user-friendly way:
        adding, reordering, and removing them without any manual setup.The long-term goal is to make the platform increasingly self-sustaining, so teachers spend
        less time configuring and more time teaching.
      </p>
      </div>
    `
  },

  {
    title: "Thank You",
    render: () => `
      <div style="text-align:center; font-size:1.3rem; line-height:1.6;">
        Thank you for your time 🙌<br/><br/>
        We’d love questions, feedback, or crazy ideas.<br/>
      </div>
    `
  }
];
