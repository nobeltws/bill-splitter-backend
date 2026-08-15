import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  OneToMany,
} from "typeorm";
import { Item } from "./item.entity";

@Entity("sessions")
export class Session {
  @PrimaryGeneratedColumn("uuid")
  id!: string;

  @Column({ name: "host_paynow_id", type: "varchar", length: 50 })
  hostPaynowId!: string;

  @Column({ type: "decimal", precision: 10, scale: 2, default: 0 })
  tax!: number;

  @Column({ name: "service_charge", type: "decimal", precision: 10, scale: 2, default: 0 })
  serviceCharge!: number;

  @Column({ type: "decimal", precision: 10, scale: 2, default: 0 })
  discount!: number;

  @CreateDateColumn({ name: "created_at" })
  createdAt!: Date;

  @OneToMany(() => Item, (item) => item.session, { cascade: true, eager: true })
  items!: Item[];
}
