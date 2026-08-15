import { AppDataSource } from "../db/data-source";
import { Session } from "../entities/session.entity";

export const sessionRepository = AppDataSource.getRepository(Session);

export async function createSession(data: {
  hostPaynowId: string;
  tax: number;
  serviceCharge: number;
  discount: number;
  items: { name: string; quantity: number; unitPrice: number }[];
}): Promise<Session> {
  const session = sessionRepository.create({
    hostPaynowId: data.hostPaynowId,
    tax: data.tax,
    serviceCharge: data.serviceCharge,
    discount: data.discount,
    items: data.items.map((item) => ({
      name: item.name,
      quantity: item.quantity,
      unitPrice: item.unitPrice,
    })),
  });

  return sessionRepository.save(session);
}

export async function findSessionById(id: string): Promise<Session | null> {
  return sessionRepository.findOne({
    where: { id },
    relations: { items: true },
  });
}
