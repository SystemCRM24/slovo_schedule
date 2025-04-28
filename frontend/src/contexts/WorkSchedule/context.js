import React, {useState} from "react";

export const WorkScheduleContext = React.createContext([]);

export function useCreateWorkScheduleContext(schedule) {
    const [services, setServices] = useState(schedule);
    return [services, setServices];
}
