import React from "react";
import {AllSpecialistsContext} from "./context.js";

export function AllSpecialistsContextProvider({children, specialists}) {
    return <AllSpecialistsContext.Provider value={specialists}>{children}</AllSpecialistsContext.Provider>
}

export function useAllSpecialistsContext() {
    const context = React.useContext(AllSpecialistsContext);
    if (!context) throw new Error('Use context within provider!');
    return context;
}
