// k6 configuration file to simulate user behavior
import http from "k6/http"
import { sleep } from "k6"

export const options = {
  stages: [
    { duration: "30s", target: 40 }, // Ramp-up to 19,110 concurrent users
    { duration: "10s", target: 40 }, // Maintain 19,110 users
    { duration: "5s", target: 0 }, // Ramp-down to 0 users
  ],
}

export default function () {
  // Step 1: Visit the homepage
  http.get("https://quefairedemesobjets-preprod.osc-fr1.scalingo.io/dechet/")
  console.log("Visited homepage")
  sleep(0.568) // Time spent on the page in seconds

  // Step 2: Navigate to the first detailed page
  http.get("https://quefairedemesobjets-preprod.osc-fr1.scalingo.io/papier-et-carton")
  console.log("Visited page: Papier et Carton")
  sleep(0.59) // Time spent on the page in seconds

  // Step 3: Navigate to another detailed page
  http.get("https://quefairedemesobjets-preprod.osc-fr1.scalingo.io/plastique")
  console.log("Visited page: Plastique")
  sleep(0.797) // Time spent on the page in seconds

  // Step 4: Return to homepage with a theme parameter
  http.get("https://quefairedemesobjets-preprod.osc-fr1.scalingo.io/?theme=dechets")
  console.log("Visited homepage with theme parameter")
  sleep(1.903) // Time spent on the page in seconds

  // Step 5: Visit a different detailed page
  http.get("https://quefairedemesobjets-preprod.osc-fr1.scalingo.io/verre")
  console.log("Visited page: Verre")
  sleep(1.5) // Time spent on the page in seconds

  // Simulate user leaving the page
  http.get("https://quefairedemesobjets-preprod.osc-fr1.scalingo.io/batteries")
  console.log("Visited page: Batteries")
  sleep(3.0) // Time spent on the page in seconds

  // End of scenario
}
