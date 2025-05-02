import React, { useState, useEffect } from "react";
import { Doughnut } from "react-chartjs-2";
import { Chart, ArcElement } from "chart.js";
import "./App.css";

Chart.register(ArcElement);
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WEB_URL = import.meta.env.VITE_WEB_URL || "http://localhost:3000";

// Use these constants in your API calls

const TeamMember = ({ name, role, github, linkedin, photo }) => (
  <div className="member-card">
    <img src={photo} alt={name} className="member-photo" />
    <h3>{name}</h3>
    <p>{role}</p>
    <div className="social-links">
      <a href={github} target="_blank" rel="noopener">
        GitHub
      </a>
      <a href={linkedin} target="_blank" rel="noopener">
        LinkedIn
      </a>
    </div>
  </div>
);

export default function App() {
  const [team, setTeam] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // Mock data - replace with real API calls
    setTeam([
      {
        id: 1,
        name: "Hailemichael",
        role: "Developer",
        github: "https://github.com/yourprofile",
        linkedin: "https://linkedin.com/in/yourprofile",
        photo: "https://i.imgur.com/7Q8N0xD.png",
      },
    ]);

    setStats({
      positive: 65,
      negative: 15,
      neutral: 20,
    });
  }, []);

  return (
    <div className="app-container">
      <h1>Sentiment Analysis Team</h1>

      <div className="dashboard">
        {stats && (
          <div className="chart-container">
            <Doughnut
              data={{
                labels: ["Positive", "Negative", "Neutral"],
                datasets: [
                  {
                    data: [stats.positive, stats.negative, stats.neutral],
                    backgroundColor: ["#4CAF50", "#F44336", "#9E9E9E"],
                  },
                ],
              }}
            />
          </div>
        )}

        <div className="team-grid">
          {team.map((member) => (
            <TeamMember key={member.id} {...member} />
          ))}
        </div>
      </div>
    </div>
  );
}
