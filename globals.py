# Define all global constants
STATUS_OK = 'ok'
STATUS_ERROR = 'error'
CONDOR_JOB_STATES = {
    1: 'idle',
    2: 'running',
    3: 'removed',
    4: 'completed',
    5: 'held',
    6: 'transferring_output',
    7: 'suspended',
}