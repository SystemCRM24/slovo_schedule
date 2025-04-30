import React, {useState} from "react";

export const WorkScheduleContext = React.createContext([]);

export function useCreateWorkScheduleContext(initialWorkSchedule) {
    const [workSchedule, setWorkSchedule] = useState(initialWorkSchedule);
    return [workSchedule, setWorkSchedule];
}
