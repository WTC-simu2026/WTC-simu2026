"""Reuse the read-only predecessor hash checker with the A18 protected manifest."""
import verify_aircraft_a17_preservation as inherited
from run_aircraft_a18 import OUT,guard
inherited.OUT=OUT
inherited.guard=guard
if __name__=='__main__':inherited.main()
