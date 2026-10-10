"""Read-only full hash audit of every predecessor artifact pinned before A19."""
import verify_aircraft_a17_preservation as inherited
from run_aircraft_a19 import OUT,guard
inherited.OUT=OUT
inherited.guard=guard
if __name__=='__main__':inherited.main()
