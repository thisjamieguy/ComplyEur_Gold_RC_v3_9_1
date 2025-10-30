import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

export interface TripRecord {
  id: number;
  employee_id: number;
  employee?: string | null;
  country: string;
  job_ref: string | null;
  start_date: string;
  end_date: string;
  ghosted: boolean;
  is_private?: boolean;
  purpose?: string | null;
  duration_days?: number | null;
}

export const TRIPS_QUERY_KEY = ["calendar", "trips"] as const;

const normaliseTrip = (trip: unknown): TripRecord => {
  const record = (typeof trip === "object" && trip !== null ? trip : {}) as Record<string, unknown>;

  const employeeNameValue = record.employee;
  const employeeFallbackValue = record.employee_name;

  return {
    id: Number(record.id),
    employee_id: Number(record.employee_id),
    employee:
      typeof employeeNameValue === "string"
        ? employeeNameValue
        : typeof employeeFallbackValue === "string"
        ? employeeFallbackValue
        : null,
    country: String(record.country ?? "").toUpperCase(),
    job_ref: typeof record.job_ref === "string" ? record.job_ref : "",
    start_date: String(record.start_date ?? ""),
    end_date: String(record.end_date ?? ""),
    ghosted: Boolean(record.ghosted),
    is_private: Boolean(record.is_private),
    purpose: typeof record.purpose === "string" ? record.purpose : null,
    duration_days: typeof record.duration_days === "number" ? record.duration_days : null,
  };
};

const fetchTrips = async (): Promise<TripRecord[]> => {
  const response = await fetch("/api/trips", {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Failed to load trips");
  }

  const payload = (await response.json()) as unknown;

  let tripsSource: unknown[] = [];
  if (Array.isArray(payload)) {
    tripsSource = payload;
  } else if (
    typeof payload === "object" &&
    payload !== null &&
    "trips" in payload &&
    Array.isArray((payload as { trips?: unknown }).trips)
  ) {
    tripsSource = (payload as { trips: unknown[] }).trips;
  }

  return tripsSource.map(normaliseTrip);
};

export const useTrips = () =>
  useQuery({
    queryKey: TRIPS_QUERY_KEY,
    queryFn: fetchTrips,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

type UpdateTripPayload = {
  id: number;
  patch: Partial<
    Pick<TripRecord, "start_date" | "end_date" | "employee_id" | "country" | "job_ref" | "ghosted" | "purpose">
  >;
};

const apiPatchTrip = async ({ id, patch }: UpdateTripPayload): Promise<TripRecord> => {
  const response = await fetch(`/api/trips/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(patch),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Failed to update trip");
  }

  return normaliseTrip(await response.json());
};

export const useUpdateTrip = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiPatchTrip,
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: TRIPS_QUERY_KEY });
      const snapshot = queryClient.getQueryData<TripRecord[]>(TRIPS_QUERY_KEY);

      if (snapshot) {
        const next = snapshot.map((trip) =>
          trip.id === variables.id ? { ...trip, ...variables.patch } : trip
        );
        queryClient.setQueryData(TRIPS_QUERY_KEY, next);
      }

      return { snapshot };
    },
    onError: (error, _variables, context) => {
      if (context?.snapshot) {
        queryClient.setQueryData(TRIPS_QUERY_KEY, context.snapshot);
      }
      const message = error instanceof Error ? error.message : "Failed to update trip";
      const suffix = message ? ` ${message}` : "";
      toast.error(`Server error 🔁 rollbacked.${suffix}`);
    },
    onSuccess: (updatedTrip) => {
      queryClient.setQueryData<TripRecord[]>(TRIPS_QUERY_KEY, (current) => {
        if (!current) return current;
        return current.map((trip) => (trip.id === updatedTrip.id ? updatedTrip : trip));
      });
      toast.success("Trip updated ✅");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: TRIPS_QUERY_KEY });
    },
  });
};

type CreateTripPayload = Partial<TripRecord> & {
  employee_id: number;
  start_date: string;
  end_date: string;
};

const apiCreateTrip = async (payload: CreateTripPayload): Promise<TripRecord> => {
  const response = await fetch("/api/trips", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Failed to create trip");
  }

  return normaliseTrip(await response.json());
};

export const useCreateTrip = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiCreateTrip,
    onSuccess: (createdTrip) => {
      queryClient.setQueryData<TripRecord[]>(TRIPS_QUERY_KEY, (current) => {
        if (!current) return current;
        return [...current, createdTrip];
      });
      toast.success("Trip created");
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Failed to create trip";
      toast.error(message);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: TRIPS_QUERY_KEY });
    },
  });
};

const apiDeleteTrip = async (id: number): Promise<number> => {
  const response = await fetch(`/api/trips/${id}`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Failed to delete trip");
  }

  return id;
};

export const useDeleteTrip = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiDeleteTrip,
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: TRIPS_QUERY_KEY });
      const snapshot = queryClient.getQueryData<TripRecord[]>(TRIPS_QUERY_KEY);
      if (snapshot) {
        queryClient.setQueryData<TripRecord[]>(TRIPS_QUERY_KEY, snapshot.filter((trip) => trip.id !== id));
      }
      return { snapshot };
    },
    onError: (error, _id, context) => {
      if (context?.snapshot) {
        queryClient.setQueryData(TRIPS_QUERY_KEY, context.snapshot);
      }
      const message = error instanceof Error ? error.message : "Failed to delete trip";
      toast.error(message);
    },
    onSuccess: () => {
      toast.success("Trip deleted");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: TRIPS_QUERY_KEY });
    },
  });
};

const apiDuplicateTrip = async ({ id, overrides }: { id: number; overrides?: Partial<CreateTripPayload> }): Promise<TripRecord> => {
  const response = await fetch(`/api/trips/${id}/duplicate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(overrides ?? {}),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Failed to duplicate trip");
  }

  return normaliseTrip(await response.json());
};

export const useDuplicateTrip = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiDuplicateTrip,
    onSuccess: (trip) => {
      queryClient.setQueryData<TripRecord[]>(TRIPS_QUERY_KEY, (current) => {
        if (!current) return current;
        return [...current, trip];
      });
      toast.success("Trip duplicated");
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Failed to duplicate trip";
      toast.error(message);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: TRIPS_QUERY_KEY });
    },
  });
};

export const useToggleGhost = () => {
  const updateTrip = useUpdateTrip();
  return (trip: TripRecord) =>
    updateTrip.mutate({ id: trip.id, patch: { ghosted: !trip.ghosted } });
};

