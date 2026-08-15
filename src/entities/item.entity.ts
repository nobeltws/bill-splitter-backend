import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToOne,
  JoinColumn,
} from "typeorm";
import { Session } from "./session.entity";

@Entity("items")
export class Item {
  @PrimaryGeneratedColumn("uuid")
  id!: string;

  @Column({ type: "varchar", length: 255 })
  name!: string;

  @Column({ type: "int" })
  quantity!: number;

  @Column({ name: "unit_price", type: "decimal", precision: 10, scale: 2 })
  unitPrice!: number;

  @ManyToOne(() => Session, (session) => session.items, { onDelete: "CASCADE" })
  @JoinColumn({ name: "session_id" })
  session!: Session;
}
