import { useQuery } from "@tanstack/react-query";

export type EmployeeRecord = {
  id: number;
  name: string;
  active?: boolean;
};

const EMPLOYEES_QUERY_KEY = ["calendar", "employees"] as const;

const normaliseEmployee = (raw: unknown): EmployeeRecord => {
  const record = (typeof raw === "object" && raw !== null ? raw : {}) as Record<string, unknown>;
  const idValue = record.id;
  const nameValue = record.name;
  const activeValue = record.active;

  const id = Number(idValue);
  const name = typeof nameValue === "string" ? nameValue.trim() : String(nameValue ?? "");
  return {
    id: Number.isFinite(id) ? id : -1,
    name: name.length > 0 ? name : "Unnamed",
    active: activeValue === undefined ? true : Boolean(activeValue),
  };
};

const fetchEmployees = async (): Promise<EmployeeRecord[]> => {
  const response = await fetch("/api/employees", {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Failed to load employees");
  }

  const payload = (await response.json()) as unknown;

  let list: unknown[] = [];
  if (Array.isArray(payload)) {
    list = payload;
  } else if (
    typeof payload === "object" &&
    payload !== null &&
    "employees" in payload &&
    Array.isArray((payload as { employees?: unknown }).employees)
  ) {
    list = (payload as { employees: unknown[] }).employees;
  }

  return list.map(normaliseEmployee);
};

export const useEmployees = () =>
  useQuery({
    queryKey: EMPLOYEES_QUERY_KEY,
    queryFn: fetchEmployees,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });


