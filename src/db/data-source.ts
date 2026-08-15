import "reflect-metadata";
import { DataSource } from "typeorm";
import { config } from "../config";

export const AppDataSource = new DataSource({
  type: "postgres",
  url: config.databaseUrl,
  synchronize: false,
  logging: config.nodeEnv === "development",
  entities: [__dirname + "/../entities/**/*.{ts,js}"],
  migrations: [__dirname + "/../../migrations/**/*.{ts,js}"],
});
