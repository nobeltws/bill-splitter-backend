import "reflect-metadata";
import app from "./app";
import { config } from "./config";
import { AppDataSource } from "./db/data-source";

async function start(): Promise<void> {
  try {
    await AppDataSource.initialize();
    console.log("Database connected");
  } catch (err) {
    console.error("Failed to connect to database:", err);
    process.exit(1);
  }

  app.listen(config.port, () => {
    console.log(`Server running on port ${config.port}`);
  });
}

start();
