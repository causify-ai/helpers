import builtins
import datetime
import logging
from typing import Any, Dict

import omegaconf as omgcfg
import pandas as pd

_LOG = logging.getLogger(__name__)

# #############################################################################
# Utility functions
# #############################################################################

def as_tuple(*args: Any) -> Dict:
    """
    Generates a Hydra recipe to build a real Python tuple.
    
    Note: builtins.tuple() expects exactly ONE iterable.
    So as_tuple("close", "volume") creates tuple(["close", "volume"]).
    """
    return {"_target_": "builtins.tuple", "_args_": [list(args)]}

# #############################################################################
# Resolvers
# #############################################################################

_RESOLVERS_REGISTERED = False

def register_custom_resolvers() -> None:
    """
    Registers all global OmegaConf resolvers. 

    This is safe to call multiple times, but will only execute once.
    """
    global _RESOLVERS_REGISTERED
    if _RESOLVERS_REGISTERED:
        return
    _LOG.debug("Registering global OmegaConf resolvers.")
    # Safely parse strings to datetime.time.
    omgcfg.OmegaConf.register_new_resolver(
        "to_time", 
        lambda s: datetime.datetime.strptime(s, "%H:%M").time(), 
        replace=True
    )
    # Safely fetch Python built-in classes like ValueError.
    omgcfg.OmegaConf.register_new_resolver(
        "builtin", 
        lambda name: getattr(builtins, name), 
        replace=True
    )
    omgcfg.OmegaConf.register_new_resolver(                                                                                                                                                                                                                                      
        "to_timestamp",                                                                                                                                                                                                                                                          
        lambda s, tz=None: pd.Timestamp(s, tz=tz) if tz else pd.Timestamp(s),                                                                                                                                                                                                    
        replace=True                                                                                                                                                                                                                                                             
    )  
    omgcfg.OmegaConf.register_new_resolver(                                                                                                                                                                                                                                     
        "to_timedelta",                                                                                                                                                                                                                                                         
        lambda s: pd.Timedelta(s),                                                                                                                                                                                                                                              
        replace=True                                                                                                                                                                                                                                                            
    )  
    _RESOLVERS_REGISTERED = True